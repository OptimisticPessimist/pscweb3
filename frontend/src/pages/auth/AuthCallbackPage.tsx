import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { useTranslation } from 'react-i18next';

export const AuthCallbackPage = () => {
    const { t } = useTranslation();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { login } = useAuth();

    useEffect(() => {
        const token = searchParams.get('token');
        if (token) {
            login(token); // AuthContextにトークンを保存
            navigate('/dashboard', { replace: true });
        } else {
            // トークンがない場合はエラー扱い(ログイン画面へ戻す)
            console.error('No token found in callback URL');
            navigate('/login', { replace: true });
        }
    }, [searchParams, login, navigate]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
            <div className="flex flex-col items-center space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
                <p className="text-gray-400">{t('auth.authenticating')}</p>
            </div>
        </div>
    );
};
