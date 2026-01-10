import React, { useEffect, useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
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
    });
  }

  return candidates;
}

export default function PollPlaceholder() {
  const { sessionId: pathSessionId } = useParams();
  const [status, setStatus] = useState('');
  const [lineUserId, setLineUserId] = useState('');
  const [sessionId, setSessionId] = useState(pathSessionId || '');
  const [selectedCandidates, setSelectedCandidates] = useState(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 候補日時リストを生成（メモ化）
  const candidates = useMemo(() => generateDefaultCandidates(), []);

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
          setStatus('LIFF SDKが読み込めていません。ローカル開発モードで動作します。');
        }
        return;
      }
      if (!liffId) {
        if (isMounted) {
          setStatus('LIFF IDが設定されていません。ローカル開発モードで動作します。');
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

        // バックエンドにLINEユーザー情報を登録
        await fetch(`${backendUrl}/api/line/link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            line_user_id: profile.userId,
            display_name: profile.displayName,
            picture_url: profile.pictureUrl,
            session_id: sessionId || null,
          }),
        });
      } catch (error) {
        if (isMounted) {
          setStatus('LIFF初期化に失敗しました。ローカル開発モードで動作します。');
        }
      }
    };

    initLiff();
    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  // チェックボックスの切り替え
  const handleToggleCandidate = (candidateId) => {
    setSelectedCandidates((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(candidateId)) {
        newSet.delete(candidateId);
      } else {
        newSet.add(candidateId);
      }
      return newSet;
    });
  };

  // 投票ボタン押下時の処理
  const handleSubmitVote = async () => {
    if (selectedCandidates.size === 0) return;

    setIsSubmitting(true);

    // 選択された日程をログ出力
    const selectedItems = candidates.filter((c) => selectedCandidates.has(c.id));
    console.log('選択された日程:', selectedItems.map((c) => c.label));
    console.log('LINE User ID:', lineUserId);
    console.log('Session ID:', sessionId);

    try {
      // Google認証URLを取得してリダイレクト
      const response = await axios.get(`${backendUrl}/api/auth/google/login`, {
        withCredentials: true,
      });

      if (response.data.authUrl) {
        window.location.href = response.data.authUrl;
      } else {
        setStatus('認証URLの取得に失敗しました。');
        setIsSubmitting(false);
      }
    } catch (error) {
      console.error('Google認証の開始に失敗しました:', error);
      setStatus('認証の開始に失敗しました。もう一度お試しください。');
      setIsSubmitting(false);
    }
  };

  const isButtonEnabled = selectedCandidates.size > 0 && !isSubmitting;

  return (
    <div className="min-h-screen bg-gray-100 font-sans">
      {/* ヘッダー */}
      <header className="bg-line-green text-white py-6 px-5 text-center">
        <h1 className="text-2xl font-bold mb-2">📅 日程調整</h1>
        <p className="text-sm opacity-90">
          参加可能な日程を選択してください
        </p>
      </header>

      {/* ステータスメッセージ */}
      {status && (
        <div className="bg-yellow-100 text-yellow-800 py-3 px-5 text-sm text-center">
          {status}
        </div>
      )}

      {/* 候補日時リスト */}
      <div className="p-4 flex flex-col gap-3">
        {candidates.map((candidate) => {
          const isSelected = selectedCandidates.has(candidate.id);
          return (
            <label
              key={candidate.id}
              className={`
                flex items-center bg-white rounded-xl py-4 px-5 
                shadow-sm cursor-pointer transition-all duration-200 
                border-2 
                ${isSelected 
                  ? 'bg-line-green-light border-line-green' 
                  : 'border-transparent hover:border-gray-200'}
              `}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => handleToggleCandidate(candidate.id)}
                className="w-6 h-6 mr-4 accent-line-green cursor-pointer"
              />
              <span className="flex-1 flex flex-col gap-1">
                <span className="text-base font-semibold text-gray-800">
                  {candidate.label.split(' ')[0]}
                </span>
                <span className="text-sm text-gray-500">
                  {candidate.label.split(' ')[1]}
                </span>
              </span>
              {isSelected && (
                <span className="text-line-green text-xl font-bold">✓</span>
              )}
            </label>
          );
        })}
      </div>

      {/* 選択数表示 */}
      <div className="py-3 px-5 text-center">
        <span className="inline-block bg-line-green text-white py-2 px-4 rounded-full text-sm font-medium">
          {selectedCandidates.size}件選択中
        </span>
      </div>

      {/* 固定フッター */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white py-4 px-5 shadow-[0_-2px_10px_rgba(0,0,0,0.1)] z-50">
        <button
          onClick={handleSubmitVote}
          disabled={!isButtonEnabled}
          className={`
            w-full py-4 px-6 text-lg font-bold text-white 
            rounded-xl transition-all duration-200
            ${isButtonEnabled 
              ? 'bg-line-green cursor-pointer active:scale-[0.98]' 
              : 'bg-gray-300 cursor-not-allowed'}
          `}
        >
          {isSubmitting ? '処理中...' : '投票してカレンダー連携へ'}
        </button>
      </footer>

      {/* フッター分のスペーサー */}
      <div className="h-24" />
    </div>
  );
}
