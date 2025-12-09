import axios from 'axios';

// Simplified for stability: Use proxy path /api
const API_URL = '/api';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request Interceptor: JWTトークンがあればヘッダーに付与
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response Interceptor: 401エラー（認証切れ）のハンドリング
apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            // トークンを削除してログイン画面へリダイレクトなどの処理
            // ここでは単純にPromiseをrejectし、呼び出し元またはAuthContextで処理する
            console.warn('Unauthorized access. Token might be invalid or expired.');
        }
        return Promise.reject(error);
    }
);
