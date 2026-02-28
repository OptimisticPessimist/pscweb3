/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { User } from '../types';
import { authApi } from '../api/auth';
import { apiClient } from '@/api/client';

interface AuthContextType {
    user: User | undefined;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (token: string) => void;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const queryClient = useQueryClient();
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

    // トークン変更時にヘッダーとLocalStorageを同期
    useEffect(() => {
        if (token) {
            localStorage.setItem('token', token);
            apiClient.defaults.headers.Authorization = `Bearer ${token}`;
        } else {
            localStorage.removeItem('token');
            delete apiClient.defaults.headers.Authorization;
        }
    }, [token]);

    // ユーザー情報の取得（トークンがある場合のみ）
    const { data: user, isLoading, isError } = useQuery({
        queryKey: ['auth', 'user'],
        queryFn: authApi.getUser,
        enabled: !!token,
        retry: false,
    });

    // 認証エラー時はログアウト扱い
    useEffect(() => {
        if (isError) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setToken(null);
        }
    }, [isError]);

    const login = (newToken: string) => {
        setToken(newToken);
    };

    const logout = () => {
        setToken(null);
        queryClient.clear();
    };

    const refreshUser = async () => {
        await queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: !!user,
                login,
                logout,
                refreshUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
