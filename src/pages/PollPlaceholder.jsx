import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const liffId = process.env.REACT_APP_LIFF_ID || '';

const getWindowLiff = () => window.liff;

export default function PollPlaceholder() {
  const { sessionId: pathSessionId } = useParams();
  const [status, setStatus] = useState('初期化中...');
  const [lineUserId, setLineUserId] = useState('');
  const [sessionId, setSessionId] = useState(pathSessionId || '');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const querySessionId = params.get('sessionId') || '';
    if (!pathSessionId && querySessionId) {
      setSessionId(querySessionId);
    }
  }, [pathSessionId]);

  useEffect(() => {
    let isMounted = true;

    const initLiff = async () => {
      const liff = getWindowLiff();
      if (!liff) {
        if (isMounted) {
          setStatus('LIFF SDKが読み込めていません。');
        }
        return;
      }
      if (!liffId) {
        if (isMounted) {
          setStatus('LIFF IDが設定されていません。');
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
        setStatus('LINEユーザー情報を取得しました。');

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

  return (
    <div style={{ padding: '32px', fontFamily: 'sans-serif' }}>
      <h1>投票ページは準備中です</h1>
      <p>このページは今後、投票UIが追加されます。</p>
      <p>しばらくお待ちください。</p>
      <p>状態: {status}</p>
      {lineUserId ? <p>LINE userId: {lineUserId}</p> : null}
    </div>
  );
}
