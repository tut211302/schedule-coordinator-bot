import React, { useState, useCallback, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

// Hotpepper ジャンルコード
const GENRE_OPTIONS = [
  { value: '', label: '選択してください' },
  { value: 'G001', label: '居酒屋' },
  { value: 'G002', label: 'ダイニングバー・バル' },
  { value: 'G003', label: '和食' },
  { value: 'G004', label: 'イタリアン・フレンチ' },
  { value: 'G005', label: '中華' },
  { value: 'G006', label: '焼肉・ホルモン' },
  { value: 'G007', label: '韓国料理' },
  { value: 'G008', label: 'アジア・エスニック料理' },
  { value: 'G009', label: '各国料理' },
  { value: 'G010', label: 'カラオケ・パーティ' },
  { value: 'G011', label: 'バー・カクテル' },
  { value: 'G012', label: 'ラーメン' },
  { value: 'G013', label: 'お好み焼き・もんじゃ' },
  { value: 'G014', label: 'カフェ・スイーツ' },
  { value: 'G017', label: 'その他グルメ' },
];

// Hotpepper 予算コード
const BUDGET_OPTIONS = [
  { value: '', label: '指定なし' },
  { value: 'B009', label: '〜1500円' },
  { value: 'B010', label: '1501〜2000円' },
  { value: 'B011', label: '2001〜3000円' },
  { value: 'B001', label: '3001〜4000円' },
  { value: 'B002', label: '4001〜5000円' },
  { value: 'B003', label: '5001〜7000円' },
  { value: 'B008', label: '7001〜10000円' },
  { value: 'B004', label: '10001〜15000円' },
  { value: 'B005', label: '15001〜20000円' },
  { value: 'B006', label: '20001〜30000円' },
  { value: 'B012', label: '30001円〜' },
];

// 人気エリアのサジェスト
const POPULAR_AREAS = [
  '渋谷', '新宿', '池袋', '銀座', '六本木',
  '恵比寿', '品川', '上野', '秋葉原', '横浜',
];

export default function ShopSurvey() {
  const { sessionId: pathSessionId } = useParams();
  const [searchParams] = useSearchParams();
  
  // セッションID
  const sessionId = pathSessionId || searchParams.get('sessionId') || null;
  
  // LINE ユーザーID
  const [lineUserId, setLineUserId] = useState('');
  
  // フォームの状態
  const [area, setArea] = useState('');
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [budget, setBudget] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAreaSuggestions, setShowAreaSuggestions] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [status, setStatus] = useState('');

  // LIFF初期化 or ローカルストレージからユーザーID取得
  useEffect(() => {
    const initUser = async () => {
      // ローカルストレージからユーザーIDを取得
      const storedUserId = localStorage.getItem('lineUserId');
      if (storedUserId) {
        setLineUserId(storedUserId);
        return;
      }

      // LIFFから取得を試みる
      const liff = window.liff;
      if (liff) {
        try {
          const liffId = process.env.REACT_APP_LIFF_ID;
          if (liffId) {
            await liff.init({ liffId });
            if (liff.isLoggedIn()) {
              const profile = await liff.getProfile();
              setLineUserId(profile.userId);
              localStorage.setItem('lineUserId', profile.userId);
            }
          }
        } catch (error) {
          console.log('LIFF初期化スキップ（ローカル開発モード）');
        }
      }
      
      // フォールバック: anonymous + タイムスタンプ
      if (!storedUserId) {
        const anonymousId = `anonymous_${Date.now()}`;
        setLineUserId(anonymousId);
        localStorage.setItem('lineUserId', anonymousId);
      }
    };

    initUser();
  }, []);

  // ジャンルのトグル
  const handleGenreToggle = useCallback((genreCode) => {
    setSelectedGenres((prev) => {
      if (prev.includes(genreCode)) {
        return prev.filter((g) => g !== genreCode);
      }
      // 最大3つまで選択可能
      if (prev.length >= 3) {
        return prev;
      }
      return [...prev, genreCode];
    });
  }, []);

  // エリアのクイック選択
  const handleAreaQuickSelect = useCallback((selectedArea) => {
    setArea(selectedArea);
    setShowAreaSuggestions(false);
  }, []);

  // フォーム送信（DBに保存）
  const handleSubmit = async () => {
    setIsSubmitting(true);
    setStatus('');

    try {
      const requestData = {
        line_user_id: lineUserId || 'anonymous_user',
        session_id: sessionId ? parseInt(sessionId, 10) : null,
        area: area.trim() || null,
        genre_codes: selectedGenres.length > 0 ? selectedGenres : null,
        budget_code: budget || null,
      };

      console.log('送信データ:', requestData);

      await axios.post(`${backendUrl}/api/survey/conditions`, requestData, {
        withCredentials: true,
      });

      setIsSaved(true);
      setStatus('✅ 条件を保存しました！');

      // 3秒後にLIFFウィンドウを閉じる（LIFFの場合）
      setTimeout(() => {
        if (window.liff && window.liff.isInClient && window.liff.isInClient()) {
          window.liff.closeWindow();
        }
      }, 2000);

    } catch (error) {
      console.error('保存に失敗:', error);
      setStatus('保存に失敗しました。もう一度お試しください。');
    } finally {
      setIsSubmitting(false);
    }
  };

  // スキップ（条件なしで完了）
  const handleSkip = async () => {
    setIsSubmitting(true);
    setStatus('');

    try {
      // 空の条件を保存（スキップしたことを記録）
      await axios.post(`${backendUrl}/api/survey/conditions`, {
        line_user_id: lineUserId || 'anonymous_user',
        session_id: sessionId ? parseInt(sessionId, 10) : null,
        area: null,
        genre_codes: null,
        budget_code: null,
      }, {
        withCredentials: true,
      });

      setIsSaved(true);
      setStatus('✅ 回答を完了しました！');

      setTimeout(() => {
        if (window.liff && window.liff.isInClient && window.liff.isInClient()) {
          window.liff.closeWindow();
        }
      }, 2000);

    } catch (error) {
      console.error('スキップ処理に失敗:', error);
      setStatus('エラーが発生しました。');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ジャンル名を取得
  const getGenreName = (code) => {
    const genre = GENRE_OPTIONS.find((g) => g.value === code);
    return genre ? genre.label : code;
  };

  // 何か入力があるかチェック
  const hasAnyInput = area.trim() || selectedGenres.length > 0 || budget;

  return (
    <div className="min-h-screen bg-gray-50 font-sans pb-40">
      {/* ヘッダー */}
      <header className="bg-line-green text-white py-6 px-5 text-center shadow-md">
        <h1 className="text-2xl font-bold mb-2">🍽️ お店の条件</h1>
        <p className="text-sm opacity-90">
          希望があれば入力してください（任意）
        </p>
      </header>

      {/* ステータスメッセージ */}
      {status && (
        <div className={`py-3 px-5 text-sm ${
          status.includes('✅') 
            ? 'bg-green-50 border-l-4 border-green-400 text-green-800'
            : 'bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800'
        }`}>
          {status}
        </div>
      )}

      {/* 完了メッセージ */}
      {isSaved && (
        <div className="p-8 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">回答完了！</h2>
          <p className="text-gray-600">
            全員の投票が完了すると、<br />
            条件に合うお店がLINEに届きます。
          </p>
        </div>
      )}

      {/* メインコンテンツ（保存前のみ表示） */}
      {!isSaved && (
        <div className="p-4 flex flex-col gap-6">
          
          {/* エリア入力 */}
          <section className="bg-white rounded-2xl p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              📍 エリア
              <span className="ml-2 text-xs font-normal text-gray-400">任意</span>
            </label>
            <div className="relative">
              <input
                type="text"
                value={area}
                onChange={(e) => setArea(e.target.value)}
                onFocus={() => setShowAreaSuggestions(true)}
                onBlur={() => setTimeout(() => setShowAreaSuggestions(false), 200)}
                placeholder="例：渋谷、新宿、銀座"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-line-green focus:outline-none transition-colors text-base"
              />
              {area && (
                <button
                  type="button"
                  onClick={() => setArea('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              )}
            </div>
            
            {/* エリアサジェスト */}
            {showAreaSuggestions && (
              <div className="mt-3">
                <p className="text-xs text-gray-500 mb-2">人気のエリア</p>
                <div className="flex flex-wrap gap-2">
                  {POPULAR_AREAS.map((popularArea) => (
                    <button
                      key={popularArea}
                      type="button"
                      onClick={() => handleAreaQuickSelect(popularArea)}
                      className={`
                        px-3 py-1.5 rounded-full text-sm font-medium transition-all
                        ${area === popularArea
                          ? 'bg-line-green text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}
                      `}
                    >
                      {popularArea}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* ジャンル選択 */}
          <section className="bg-white rounded-2xl p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              🍴 ジャンル
              <span className="ml-2 text-xs font-normal text-gray-400">任意・最大3つ</span>
            </label>
            <p className="text-xs text-gray-500 mb-3">食べたいジャンルがあれば選択</p>
            
            <div className="flex flex-wrap gap-2">
              {GENRE_OPTIONS.filter((g) => g.value).map((genre) => {
                const isSelected = selectedGenres.includes(genre.value);
                const isDisabled = !isSelected && selectedGenres.length >= 3;
                
                return (
                  <button
                    key={genre.value}
                    type="button"
                    onClick={() => handleGenreToggle(genre.value)}
                    disabled={isDisabled}
                    className={`
                      px-4 py-2 rounded-full text-sm font-medium transition-all
                      ${isSelected
                        ? 'bg-line-green text-white shadow-sm'
                        : isDisabled
                          ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200 active:scale-95'}
                    `}
                  >
                    {isSelected && '✓ '}
                    {genre.label}
                  </button>
                );
              })}
            </div>
            
            {/* 選択中のジャンル表示 */}
            {selectedGenres.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-2">選択中: {selectedGenres.length}/3</p>
                <div className="flex flex-wrap gap-2">
                  {selectedGenres.map((code) => (
                    <span
                      key={code}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-green-50 text-line-green rounded-full text-sm font-medium"
                    >
                      {getGenreName(code)}
                      <button
                        type="button"
                        onClick={() => handleGenreToggle(code)}
                        className="ml-1 hover:text-green-700"
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* 予算選択 */}
          <section className="bg-white rounded-2xl p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              💰 予算（1人あたり）
              <span className="ml-2 text-xs font-normal text-gray-400">任意</span>
            </label>
            <div className="relative">
              <select
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-line-green focus:outline-none transition-colors text-base appearance-none bg-white cursor-pointer"
              >
                {BUDGET_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            
            {/* よく使う予算帯のクイック選択 */}
            <div className="mt-3">
              <p className="text-xs text-gray-500 mb-2">よく選ばれる予算</p>
              <div className="flex flex-wrap gap-2">
                {['B011', 'B001', 'B002', 'B003'].map((code) => {
                  const option = BUDGET_OPTIONS.find((b) => b.value === code);
                  if (!option) return null;
                  return (
                    <button
                      key={code}
                      type="button"
                      onClick={() => setBudget(code)}
                      className={`
                        px-3 py-1.5 rounded-full text-sm font-medium transition-all
                        ${budget === code
                          ? 'bg-line-green text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}
                      `}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          {/* 選択内容のサマリー */}
          {hasAnyInput && (
            <section className="bg-blue-50 rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-blue-800 mb-3">📋 あなたの希望</h3>
              <div className="space-y-2 text-sm text-blue-700">
                {area && (
                  <div className="flex items-start gap-2">
                    <span className="text-blue-500">📍</span>
                    <span>{area}</span>
                  </div>
                )}
                {selectedGenres.length > 0 && (
                  <div className="flex items-start gap-2">
                    <span className="text-blue-500">🍴</span>
                    <span>{selectedGenres.map((code) => getGenreName(code)).join('、')}</span>
                  </div>
                )}
                {budget && (
                  <div className="flex items-start gap-2">
                    <span className="text-blue-500">💰</span>
                    <span>{BUDGET_OPTIONS.find((b) => b.value === budget)?.label}</span>
                  </div>
                )}
              </div>
            </section>
          )}
        </div>
      )}

      {/* 固定フッター */}
      {!isSaved && (
        <footer className="fixed bottom-0 left-0 right-0 bg-white py-4 px-5 shadow-[0_-4px_20px_rgba(0,0,0,0.1)] z-50 border-t border-gray-100">
          <div className="max-w-lg mx-auto space-y-3">
            {/* メインボタン */}
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className={`
                w-full py-4 px-6 text-lg font-bold text-white 
                rounded-2xl transition-all duration-200 shadow-lg
                ${!isSubmitting
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
                  保存中...
                </span>
              ) : hasAnyInput ? (
                '✅ この条件で回答する'
              ) : (
                '✅ 条件なしで回答する'
              )}
            </button>
            
            {/* スキップボタン */}
            {hasAnyInput && (
              <button
                onClick={handleSkip}
                disabled={isSubmitting}
                className="w-full py-3 px-6 text-sm font-medium text-gray-500 
                  rounded-xl transition-all hover:bg-gray-100"
              >
                条件をクリアして回答する
              </button>
            )}
            
            <p className="text-xs text-gray-400 text-center">
              条件は任意です。入力しなくても回答できます。
            </p>
          </div>
        </footer>
      )}
    </div>
  );
}
