// API通信用のaxiosインスタンスとヘルパー関数

import axios from 'axios';

const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

// axiosインスタンスを作成
const apiClient = axios.create({
  baseURL: backendUrl,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター（必要に応じてトークンを追加）
apiClient.interceptors.request.use(
  (config) => {
    // 必要に応じてトークンを追加
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター（エラーハンドリング）
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 認証エラーの場合の処理
      console.error('認証エラー: ログインが必要です');
    }
    return Promise.reject(error);
  }
);

// API関数
export const googleAuthApi = {
  // Google認証開始URLを取得
  getAuthUrl: async () => {
    const response = await apiClient.get('/api/auth/google/login');
    return response.data;
  },

  // 認証コールバック処理
  handleCallback: async (code, state) => {
    const response = await apiClient.post('/api/auth/google/callback', {
      code,
      state,
    });
    return response.data;
  },

  // カレンダー連携状態を取得
  getConnectionStatus: async () => {
    const response = await apiClient.get('/api/user/calendar-status');
    return response.data;
  },

  // 連携を解除
  disconnect: async () => {
    const response = await apiClient.post('/api/auth/google/disconnect');
    return response.data;
  },
};

export default apiClient;
