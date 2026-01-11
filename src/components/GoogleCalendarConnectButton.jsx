import React, { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

const GoogleCalendarConnectButton = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userEmail, setUserEmail] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

  const checkConnectionStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${backendUrl}/api/user/calendar-status`, {
        withCredentials: true,
      });
      setIsConnected(response.data.isConnected);
      setUserEmail(response.data.email);
      setError(null);
    } catch (err) {
      console.error('連携状態の取得に失敗しました:', err);
      setIsConnected(false);
      setUserEmail(null);
      setError(null);
    } finally {
      setLoading(false);
    }
  }, [backendUrl]);

  useEffect(() => {
    checkConnectionStatus();
  }, [checkConnectionStatus]);

  const handleConnect = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${backendUrl}/api/auth/google/login`, {
        withCredentials: true,
      });
      window.location.href = response.data.authUrl;
    } catch (err) {
      console.error('認証の開始に失敗しました:', err);
      setError('認証の開始に失敗しました。もう一度お試しください。');
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setError(null);
      await axios.post(
        `${backendUrl}/api/auth/google/disconnect`,
        {},
        { withCredentials: true }
      );
      setIsConnected(false);
      setUserEmail(null);
      alert('連携を解除しました。');
    } catch (err) {
      console.error('連携の解除に失敗しました:', err);
      setError('連携の解除に失敗しました。もう一度お試しください。');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>読み込み中...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Googleカレンダー連携</h2>

        {error && <div style={styles.error}>{error}</div>}

        {isConnected ? (
          <div style={styles.connectedSection}>
            <div style={styles.statusBadge}>
              <span style={styles.statusDot}>●</span> 連携済み
            </div>
            {userEmail && (
              <p style={styles.emailText}>
                連携中のアカウント: <strong>{userEmail}</strong>
              </p>
            )}
            <p style={styles.description}>
              Googleカレンダーと連携されています。イベントの作成や管理が可能です。
            </p>
            <button
              onClick={handleDisconnect}
              style={styles.disconnectButton}
              disabled={loading}
            >
              連携を解除
            </button>
          </div>
        ) : (
          <div style={styles.disconnectedSection}>
            <div style={styles.statusBadge}>
              <span style={{ ...styles.statusDot, color: '#999' }}>●</span> 未連携
            </div>
            <p style={styles.description}>
              Googleカレンダーとの連携を開始するには、下のボタンをクリックしてGoogleアカウントでログインしてください。
            </p>
            <button
              onClick={handleConnect}
              style={styles.connectButton}
              disabled={loading}
            >
              <svg style={styles.googleIcon} viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Googleカレンダーと連携する
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

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
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '20px',
    textAlign: 'center',
    color: '#333',
  },
  loading: {
    textAlign: 'center',
    padding: '20px',
    color: '#666',
  },
  error: {
    backgroundColor: '#fee',
    border: '1px solid #fcc',
    borderRadius: '4px',
    padding: '12px',
    marginBottom: '20px',
    color: '#c33',
  },
  statusBadge: {
    display: 'inline-block',
    padding: '8px 16px',
    borderRadius: '20px',
    backgroundColor: '#e8f5e9',
    color: '#2e7d32',
    fontSize: '14px',
    fontWeight: '500',
    marginBottom: '16px',
  },
  statusDot: {
    marginRight: '6px',
    color: '#4caf50',
  },
  emailText: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '16px',
  },
  description: {
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#666',
    marginBottom: '24px',
  },
  connectedSection: {
    textAlign: 'center',
  },
  disconnectedSection: {
    textAlign: 'center',
  },
  connectButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    width: '100%',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: '500',
    color: '#333',
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  disconnectButton: {
    width: '100%',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: '500',
    color: 'white',
    backgroundColor: '#f44336',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  googleIcon: {
    width: '20px',
    height: '20px',
  },
};

export default GoogleCalendarConnectButton;
