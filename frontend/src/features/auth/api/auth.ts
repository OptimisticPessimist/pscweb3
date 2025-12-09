import { apiClient } from '@/api/client';
import type { User } from '../types';

export const authApi = {
    // バックエンドの /auth/login はリダイレクト用なので、フロントエンドからは直接リンクとして使用する
    // ここではコールバック後のトークン検証やユーザー取得を定義する

    getUser: async (): Promise<User> => {
        const response = await apiClient.get<User>('/users/me');
        return response.data;
    },

    // 仮にバックエンドにログアウトAPIがあれば呼ぶが、JWTなので基本はフロント側での破棄のみ
    // logout: async () => { ... }
};
