import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing'); // processing, success, error
  const [message, setMessage] = useState('認証処理中...');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      // URLからコードとstateを取得
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      // エラーがある場合
      if (error) {
        setStatus('error');
        setMessage(`認証がキャンセルされました: ${error}`);
        setTimeout(() => {
          navigate('/');
        }, 3000);
        return;
      }

      // コードがない場合
      if (!code) {
        setStatus('error');
        setMessage('認証コードが見つかりませんでした。');
        setTimeout(() => {
          navigate('/');
        }, 3000);
        return;
      }

      // バックエンドにコードとstateを送信
      setMessage('認証情報を処理しています...');
      const response = await axios.post(
        `${backendUrl}/api/auth/google/callback`,
        {
          code: code,
          state: state,
        },
        {
          withCredentials: true,
        }
      );

      if (response.data.success) {
        setStatus('success');
        setMessage('Googleカレンダーとの連携が完了しました！');
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } else {
        throw new Error(response.data.message || '認証に失敗しました');
      }
    } catch (err) {
      console.error('認証コールバック処理エラー:', err);
      setStatus('error');
      setMessage(
        err.response?.data?.message || 
        '認証処理中にエラーが発生しました。もう一度お試しください。'
      );
      setTimeout(() => {
        navigate('/');
      }, 3000);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.iconContainer}>
          {status === 'processing' && (
            <div style={styles.spinner}></div>
          )}
          {status === 'success' && (
            <div style={styles.successIcon}>✓</div>
          )}
          {status === 'error' && (
            <div style={styles.errorIcon}>✕</div>
          )}
        </div>
        
        <h2 style={styles.title}>
          {status === 'processing' && '認証処理中'}
          {status === 'success' && '連携成功'}
          {status === 'error' && '連携失敗'}
        </h2>
        
        <p style={styles.message}>{message}</p>
        
        {status !== 'processing' && (
          <button
            onClick={() => navigate('/')}
            style={styles.button}
          >
            ホームに戻る
          </button>
        )}
      </div>
    </div>
  );
};

// インラインスタイル
const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    padding: '40px',
    maxWidth: '500px',
    width: '100%',
    textAlign: 'center',
  },
  iconContainer: {
    marginBottom: '20px',
  },
  spinner: {
    width: '50px',
    height: '50px',
    margin: '0 auto',
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #4285F4',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  successIcon: {
    width: '50px',
    height: '50px',
    margin: '0 auto',
    backgroundColor: '#4caf50',
    color: 'white',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '30px',
    fontWeight: 'bold',
  },
  errorIcon: {
    width: '50px',
    height: '50px',
    margin: '0 auto',
    backgroundColor: '#f44336',
    color: 'white',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '30px',
    fontWeight: 'bold',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '16px',
    color: '#333',
  },
  message: {
    fontSize: '16px',
    lineHeight: '1.6',
    color: '#666',
    marginBottom: '24px',
  },
  button: {
    padding: '12px 32px',
    fontSize: '16px',
    fontWeight: '500',
    color: 'white',
    backgroundColor: '#4285F4',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
};

// スピナーアニメーション用のCSSを追加
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);

export default AuthCallback;
