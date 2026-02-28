import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { authApi } from '@/features/auth/api/auth';
import { Key, ShieldCheck, ShieldAlert, Save, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

export function UserSettingsPage() {
    const { t } = useTranslation();
    const { user, refreshUser } = useAuth();
    const [screenName, setScreenName] = useState(user?.screen_name || '');
    const [premiumPassword, setPremiumPassword] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);
        try {
            await authApi.updateMe({
                premium_password: premiumPassword || undefined,
                screen_name: screenName
            });
            toast.success(t('userSettings.updateSuccess'));
            setPremiumPassword('');
            await refreshUser();
        } catch (error) {
            console.error(error);
            toast.error(t('userSettings.updateError'));
        } finally {
            setIsSaving(false);
        }
    };

    if (!user) return null;

    return (
        <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <Key className="w-8 h-8 text-purple-600" />
                    {t('userSettings.title')}
                </h1>
                <p className="mt-2 text-gray-600">
                    {t('userSettings.description')}
                </p>
            </header>

            <form onSubmit={handleSave} className="space-y-8">
                <div className="bg-white shadow-xl rounded-2xl overflow-hidden border border-gray-100 p-6 sm:p-8">
                    <section>
                        <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
                            <ShieldCheck className="w-5 h-5 text-purple-500" />
                            {t('userSettings.title')}
                        </h2>

                        <div className="space-y-6">
                            <div>
                                <label htmlFor="screen_name" className="block text-sm font-medium text-gray-700 mb-2">
                                    {t('userSettings.displayName')}
                                </label>
                                <input
                                    type="text"
                                    id="screen_name"
                                    value={screenName}
                                    onChange={(e) => setScreenName(e.target.value)}
                                    className="block w-full px-4 py-3 rounded-xl border-gray-200 shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder={user.discord_username}
                                />
                            </div>

                            <hr className="border-gray-100" />

                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                    <Key className="w-5 h-5 text-purple-500" />
                                    {t('userSettings.premiumPassword')}
                                </h3>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                                    <div className="p-4 rounded-xl bg-purple-50 border border-purple-100 flex items-start gap-4">
                                        <div className={cn(
                                            "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center",
                                            user.has_premium_password ? "bg-green-100 text-green-600" : "bg-yellow-100 text-yellow-600"
                                        )}>
                                            {user.has_premium_password ? <ShieldCheck className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-bold text-gray-900">
                                                {t('userSettings.currentPasswordStatus')}
                                            </h4>
                                            <p className="text-sm text-gray-600 mt-1">
                                                {user.has_premium_password
                                                    ? t('userSettings.passwordActive')
                                                    : t('userSettings.passwordInactive')
                                                }
                                            </p>
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-100 flex items-start gap-4">
                                        <div className={cn(
                                            "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center",
                                            user.premium_tier ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-600"
                                        )}>
                                            <ShieldCheck className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-bold text-gray-900">
                                                {t('userSettings.currentRank')}
                                            </h4>
                                            <p className="text-sm text-gray-600 mt-1 font-medium capitalize">
                                                {t(`userSettings.rank_${user.premium_tier || 'none'}`)}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <label htmlFor="premium_password" className="block text-sm font-medium text-gray-700 mb-2">
                                    {t('userSettings.premiumPassword')}
                                </label>
                                <div className="relative">
                                    <input
                                        type="password"
                                        id="premium_password"
                                        value={premiumPassword}
                                        onChange={(e) => setPremiumPassword(e.target.value)}
                                        className="block w-full px-4 py-3 rounded-xl border-gray-200 shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                        placeholder="••••••••"
                                    />
                                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                                        <Key className="h-5 w-5 text-gray-400" />
                                    </div>
                                </div>
                                <p className="mt-3 text-sm text-gray-500 leading-relaxed">
                                    {t('userSettings.premiumPasswordDescription')}
                                </p>
                            </div>
                        </div>

                        <div className="pt-8 border-t border-gray-100 mt-8">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white font-bold rounded-xl shadow-lg shadow-purple-200 transition-all hover:-translate-y-0.5"
                            >
                                {isSaving ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Save className="w-5 h-5" />
                                )}
                                {t('userSettings.save')}
                            </button>
                        </div>
                    </section>
                </div>
            </form>
        </div>
    );
}
