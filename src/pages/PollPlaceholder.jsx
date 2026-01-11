import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const liffId = process.env.REACT_APP_LIFF_ID || '';

const getWindowLiff = () => window.liff;

// 曜日の日本語表記
const WEEKDAY_NAMES = ['日', '月', '火', '水', '木', '金', '土'];

/**
 * 今日から14日分の候補日時を生成する
 * - 平日 (月〜金): 19:00–21:00
 * - 週末 (土・日): 17:00–20:00
 */
function generateDefaultCandidates() {
  const candidates = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (let i = 0; i < 14; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);

    const dayOfWeek = date.getDay(); // 0=日, 1=月, ..., 6=土
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

    const startHour = isWeekend ? 17 : 19;
    const endHour = isWeekend ? 20 : 21;

    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekdayName = WEEKDAY_NAMES[dayOfWeek];

    candidates.push({
      id: `candidate-${i}`,
      date: new Date(date),
      label: `${month}月${day}日(${weekdayName}) ${startHour}:00–${endHour}:00`,
      startHour,
      endHour,
      isWeekend,
      dateString: `${date.getFullYear()}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
    });
  }

  return candidates;
}

/**
 * 投票数に応じた背景色を返す
 */
function getVoteIntensityClass(votes, maxVotes) {
  if (votes === 0 || maxVotes === 0) return '';
  const ratio = votes / maxVotes;
  if (ratio >= 0.8) return 'bg-green-100 border-green-400';
  if (ratio >= 0.5) return 'bg-green-50 border-green-300';
  if (ratio >= 0.3) return 'bg-yellow-50 border-yellow-300';
  return '';
}

export default function PollPlaceholder() {
  const { sessionId: pathSessionId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('');
  const [lineUserId, setLineUserId] = useState('');
  const [sessionId, setSessionId] = useState(pathSessionId || '');
  const [selectedCandidates, setSelectedCandidates] = useState(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // 投票状況のステート
  const [totalVoters, setTotalVoters] = useState(0);
  const [voteSummary, setVoteSummary] = useState({});
  const [votersByOption, setVotersByOption] = useState({});
  const [isLoadingSummary, setIsLoadingSummary] = useState(true);

  // Google連携ポップアップ用のstate
  const [showGooglePrompt, setShowGooglePrompt] = useState(false);
  const [isVoteSaved, setIsVoteSaved] = useState(false);

  // アンケートへの遷移確認用のstate
  const [showSurveyPrompt, setShowSurveyPrompt] = useState(false);

  // 候補日時リストを生成（メモ化）
  const candidates = useMemo(() => generateDefaultCandidates(), []);

  // 最大投票数を計算
  const maxVotes = useMemo(() => {
    const votes = Object.values(voteSummary);
    return votes.length > 0 ? Math.max(...votes) : 0;
  }, [voteSummary]);

  // 投票サマリーを取得
  const fetchVoteSummary = useCallback(async () => {
    if (!sessionId) {
      setIsLoadingSummary(false);
      return;
    }

    try {
      setIsLoadingSummary(true);
      const response = await axios.get(`${backendUrl}/api/events/${sessionId}/summary`, {
        withCredentials: true,
      });
      
      setTotalVoters(response.data.total_voters || 0);
      setVoteSummary(response.data.vote_counts || {});
      setVotersByOption(response.data.voters_by_option || {});
    } catch (error) {
      console.error('投票サマリーの取得に失敗:', error);
      // エラー時はデフォルト値を維持
    } finally {
      setIsLoadingSummary(false);
    }
  }, [sessionId]);

  // 初期ロード時とセッションID変更時にサマリーを取得
  useEffect(() => {
    fetchVoteSummary();
  }, [fetchVoteSummary]);

  // 初期状態で全ての候補を選択済みにする
  useEffect(() => {
    if (!isInitialized && candidates.length > 0) {
      const allIds = new Set(candidates.map((c) => c.id));
      setSelectedCandidates(allIds);
      setIsInitialized(true);
    }
  }, [candidates, isInitialized]);

  // クエリパラメータからsessionIdを取得
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const querySessionId = params.get('sessionId') || '';
    if (!pathSessionId && querySessionId) {
      setSessionId(querySessionId);
    }
  }, [pathSessionId]);

  // LIFF初期化
  useEffect(() => {
    let isMounted = true;

    const initLiff = async () => {
      const liff = getWindowLiff();
      if (!liff) {
        if (isMounted) {
          setStatus('ローカル開発モードで動作中');
        }
        return;
      }
      if (!liffId) {
        if (isMounted) {
          setStatus('ローカル開発モードで動作中');
        }
        return;
      }
      try {
        await liff.init({ liffId });
        if (!liff.isLoggedIn()) {
          liff.login();
          return;
        }
        const profile = await liff.getProfile();
        if (!isMounted) return;
        setLineUserId(profile.userId);
        setStatus('');

        // Register user to backend
        const response = await fetch(`${backendUrl}/api/line/link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            line_user_id: profile.userId,
            display_name: profile.displayName,
            picture_url: profile.pictureUrl,
            status_message: null,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error('Registration error:', errorData);
          if (isMounted) {
            setStatus(`登録エラー: ${errorData.detail || '不明なエラー'}`);
          }
          return;
        }

        const userData = await response.json();
        if (isMounted) {
          setStatus(`ユーザー登録完了。ID: ${userData.id}`);
        }
      } catch (error) {
        if (isMounted) {
          console.error('Error:', error);
          setStatus(`初期化または登録に失敗しました: ${error.message}`);
        }
      }
    };

    initLiff();
    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  // チェックボックスの切り替え
  const handleToggleCandidate = useCallback((candidateId) => {
    setSelectedCandidates((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(candidateId)) {
        newSet.delete(candidateId);
      } else {
        newSet.add(candidateId);
      }
      return newSet;
    });
  }, []);

  // 全選択/全解除
  const handleSelectAll = useCallback(() => {
    const allIds = new Set(candidates.map((c) => c.id));
    setSelectedCandidates(allIds);
  }, [candidates]);

  const handleDeselectAll = useCallback(() => {
    setSelectedCandidates(new Set());
  }, []);

  // 確定ボタン押下時の処理
  const handleConfirm = async () => {
    if (selectedCandidates.size === 0) {
      setStatus('少なくとも1つの日程を選択してください。');
      return;
    }

    setIsSubmitting(true);
    setStatus('');

    try {
      // 選択された日程リストを取得
      const selectedItems = candidates.filter((c) => selectedCandidates.has(c.id));
      
      const votesData = selectedItems.map((c) => ({
        date: c.label,
        start_time: `${c.dateString}T${String(c.startHour).padStart(2, '0')}:00:00`,
        end_time: `${c.dateString}T${String(c.endHour).padStart(2, '0')}:00:00`,
        is_late: false
      }));

      // DBに保存（一時的にGoogle連携チェックをスキップ）
      await axios.post(`${backendUrl}/api/events/vote`, {
        line_user_id: lineUserId || 'anonymous_user',
        session_id: sessionId ? parseInt(sessionId, 10) : null,
        votes: votesData
      }, {
        withCredentials: true
      });

      console.log('投票を保存しました:', votesData.length, '件');
      setIsVoteSaved(true);

      // 投票サマリーを更新
      await fetchVoteSummary();

      // 完了メッセージを表示して、お店アンケート画面への遷移を確認
      setStatus('✅ 投票が完了しました！');
      setIsSubmitting(false);

      // アンケートへの遷移確認ダイアログを表示
      setShowSurveyPrompt(true);

    } catch (error) {
      console.error('処理に失敗しました:', error);
      setStatus('処理に失敗しました。もう一度お試しください。');
      setIsSubmitting(false);
    }
  };

  // Google連携画面へ遷移
  const handleGoToGoogleAuth = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/auth/google/login`, {
        withCredentials: true,
      });
      if (response.data.authUrl) {
        window.location.href = response.data.authUrl;
      }
    } catch (error) {
      console.error('Google認証URLの取得に失敗:', error);
      setStatus('認証画面への遷移に失敗しました。');
    }
  };

  // ポップアップを閉じる
  const handleClosePrompt = () => {
    setShowGooglePrompt(false);
  };

  // アンケート画面へ遷移
  const handleGoToSurvey = () => {
    const surveyPath = sessionId ? `/survey/${sessionId}` : '/survey';
    navigate(surveyPath);
  };

  // アンケートをスキップ（LIFFウィンドウを閉じる or 画面に留まる）
  const handleSkipSurvey = () => {
    setShowSurveyPrompt(false);
    // LIFFの場合はウィンドウを閉じる
    if (window.liff && window.liff.isInClient && window.liff.isInClient()) {
      window.liff.closeWindow();
    }
  };

  // 候補のラベルから投票数を取得
  const getVoteCount = (label) => {
    return voteSummary[label] || 0;
  };

  // 候補のラベルから投票者を取得
  const getVoters = (label) => {
    return votersByOption[label] || [];
  };

  const isAllSelected = selectedCandidates.size === candidates.length;
  const isNoneSelected = selectedCandidates.size === 0;
  const isButtonEnabled = selectedCandidates.size > 0 && !isSubmitting;

  return (
    <div className="min-h-screen bg-gray-50 font-sans pb-32">
      {/* ヘッダー */}
      <header className="bg-line-green text-white py-6 px-5 text-center shadow-md">
        <h1 className="text-2xl font-bold mb-2">📅 候補日程の確認</h1>
        <p className="text-sm opacity-90">
          不要な日程のチェックを外してください
        </p>
      </header>

      {/* 参加状況バッジ */}
      <div className="bg-white border-b border-gray-200 py-4 px-5">
        <div className="flex items-center justify-center gap-3">
          <div className="flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-full">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
            </svg>
            <span className="font-semibold text-lg">
              {isLoadingSummary ? '...' : totalVoters}
            </span>
            <span className="text-sm">人が回答済み</span>
          </div>
        </div>
      </div>

      {/* ステータスメッセージ */}
      {status && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800 py-3 px-5 text-sm">
          {status}
        </div>
      )}

      {/* 選択操作バー */}
      <div className="sticky top-0 z-40 bg-white border-b border-gray-200 py-3 px-5 flex items-center justify-between shadow-sm">
        <span className="text-sm font-medium text-gray-700">
          {selectedCandidates.size}件 / {candidates.length}件 選択中
        </span>
        <div className="flex gap-2">
          <button
            onClick={handleSelectAll}
            disabled={isAllSelected}
            className={`
              text-xs px-3 py-1.5 rounded-full font-medium transition-all
              ${isAllSelected 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                : 'bg-line-green text-white hover:bg-green-600 active:scale-95'}
            `}
          >
            全選択
          </button>
          <button
            onClick={handleDeselectAll}
            disabled={isNoneSelected}
            className={`
              text-xs px-3 py-1.5 rounded-full font-medium transition-all
              ${isNoneSelected 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300 active:scale-95'}
            `}
          >
            全解除
          </button>
        </div>
      </div>

      {/* 候補日時リスト */}
      <div className="p-4 flex flex-col gap-3">
        {candidates.map((candidate) => {
          const isSelected = selectedCandidates.has(candidate.id);
          const voteCount = getVoteCount(candidate.label);
          const voters = getVoters(candidate.label);
          const intensityClass = getVoteIntensityClass(voteCount, maxVotes);
          const isPopular = voteCount > 0 && voteCount === maxVotes;
          
          return (
            <label
              key={candidate.id}
              className={`
                flex items-center bg-white rounded-2xl py-4 px-5 
                shadow-sm cursor-pointer transition-all duration-200 
                border-2 select-none
                ${isSelected 
                  ? `border-line-green ${intensityClass || 'bg-green-50'}` 
                  : 'border-gray-200 opacity-60 hover:opacity-80'}
              `}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => handleToggleCandidate(candidate.id)}
                className="w-6 h-6 mr-4 accent-line-green cursor-pointer flex-shrink-0"
              />
              
              <div className="flex-1 flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className={`text-base ${isSelected ? 'text-gray-800' : 'text-gray-500'} ${isPopular ? 'font-bold' : 'font-semibold'}`}>
                    {candidate.label.split(' ')[0]}
                  </span>
                  {isPopular && voteCount > 0 && (
                    <span className="text-xs bg-yellow-400 text-yellow-900 px-2 py-0.5 rounded-full font-bold">
                      🔥 人気
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm ${isSelected ? 'text-gray-600' : 'text-gray-400'}`}>
                    {candidate.label.split(' ')[1]}
                  </span>
                </div>
                
                {/* 投票者プレビュー（投票がある場合のみ） */}
                {voters.length > 0 && (
                  <div className="mt-2 flex items-center gap-1 flex-wrap">
                    {voters.slice(0, 3).map((voter, idx) => (
                      <span 
                        key={idx}
                        className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
                      >
                        {voter.display_name}
                      </span>
                    ))}
                    {voters.length > 3 && (
                      <span className="text-xs text-gray-400">
                        +{voters.length - 3}人
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* 投票数チップ */}
              <div className="flex items-center gap-2 ml-2">
                <div className={`
                  flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium
                  ${voteCount > 0 
                    ? isPopular 
                      ? 'bg-line-green text-white' 
                      : 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-400'}
                `}>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                  </svg>
                  <span>{voteCount}人</span>
                </div>
                
                {isSelected && (
                  <span className="text-line-green text-xl font-bold">✓</span>
                )}
              </div>
            </label>
          );
        })}
      </div>

      {/* プログレスサマリー */}
      {totalVoters > 0 && (
        <div className="mx-4 mb-4 bg-white rounded-2xl p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">📊 投票状況</h3>
          <div className="space-y-2">
            {candidates
              .map((c) => ({ label: c.label, votes: getVoteCount(c.label) }))
              .sort((a, b) => b.votes - a.votes)
              .slice(0, 5)
              .map((item, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-24 truncate">
                    {item.label.split(' ')[0]}
                  </span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        idx === 0 ? 'bg-line-green' : 'bg-blue-400'
                      }`}
                      style={{ 
                        width: `${maxVotes > 0 ? (item.votes / maxVotes) * 100 : 0}%` 
                      }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-600 w-8 text-right">
                    {item.votes}人
                  </span>
                </div>
              ))
            }
          </div>
        </div>
      )}

      {/* Google連携ポップアップ */}
      {showGooglePrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <div className="text-center">
              <div className="text-5xl mb-4">�</div>
              <h2 className="text-xl font-bold text-gray-800 mb-2">
                Googleカレンダー連携が必要です
              </h2>
              <p className="text-gray-600 mb-6">
                投票を完了するには、Googleカレンダーとの連携が必要です。連携すると、決定した日程が自動でカレンダーに登録されます。
              </p>
              
              <div className="flex flex-col gap-3">
                <button
                  onClick={handleGoToGoogleAuth}
                  className="w-full py-3 px-4 bg-line-green text-white font-bold rounded-xl hover:bg-green-600 transition-colors"
                >
                  Googleカレンダーと連携する
                </button>
                <button
                  onClick={handleClosePrompt}
                  className="w-full py-3 px-4 bg-gray-100 text-gray-600 font-medium rounded-xl hover:bg-gray-200 transition-colors"
                >
                  キャンセル
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* お店アンケートへの遷移確認ダイアログ */}
      {showSurveyPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <div className="text-center">
              <div className="text-5xl mb-4"></div>
              <h2 className="text-xl font-bold text-gray-800 mb-2">
                投票完了！
              </h2>
              <p className="text-gray-600 mb-6">
                お店の希望条件（エリアジャンル予算）を入力すると、条件に合ったお店をLINEでお知らせします。
              </p>
              
              <div className="flex flex-col gap-3">
                <button
                  onClick={handleGoToSurvey}
                  className="w-full py-3 px-4 bg-line-green text-white font-bold rounded-xl hover:bg-green-600 transition-colors"
                >
                   お店の条件を入力する
                </button>
                <button
                  onClick={handleSkipSurvey}
                  className="w-full py-3 px-4 bg-gray-100 text-gray-600 font-medium rounded-xl hover:bg-gray-200 transition-colors"
                >
                  スキップして終了
                </button>
              </div>
              
              <p className="text-xs text-gray-400 mt-4">
                条件は任意です。後から入力することもできます。
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 固定フッター */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white py-4 px-5 shadow-[0_-4px_20px_rgba(0,0,0,0.1)] z-50 border-t border-gray-100">
        <div className="max-w-lg mx-auto">
          <button
            onClick={handleConfirm}
            disabled={!isButtonEnabled}
            className={`
              w-full py-4 px-6 text-lg font-bold text-white 
              rounded-2xl transition-all duration-200 shadow-lg
              ${isButtonEnabled 
                ? 'bg-line-green cursor-pointer hover:bg-green-600 active:scale-[0.98] shadow-green-200' 
                : 'bg-gray-300 cursor-not-allowed shadow-none'}
            `}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                送信中...
              </span>
            ) : isVoteSaved ? (
              '✅ 投票済み'
            ) : (
              `投票する（${selectedCandidates.size}件）`
            )}
          </button>
          <p className="text-xs text-gray-400 text-center mt-2">
            {isVoteSaved 
              ? '選択を変更して再投票することもできます'
              : '選択した日程で投票します'}
          </p>
        </div>
      </footer>
    </div>
  );
}
