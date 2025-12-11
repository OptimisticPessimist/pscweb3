import { NavLink, useParams } from 'react-router-dom';
import {
    Home,
    FileText,
    Users,
    Calendar,
    Settings,
    LayoutGrid,
    Clapperboard,
    Wrench,
    ClipboardCheck
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/features/auth/hooks/useAuth';

// tailwind-merge helper
function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

export function Sidebar() {
    const { projectId } = useParams<{ projectId: string }>();
    const { t } = useTranslation();
    const { user } = useAuth();

    // プロジェクト選択中かどうかでメニューを切り替える
    // 共通メニュー
    const commonLinks = [
        { to: '/', icon: LayoutGrid, label: t('nav.dashboard') },
        { to: '/my-schedule', icon: Calendar, label: t('nav.mySchedule') },
    ];

    // プロジェクト内メニュー
    const projectLinks = projectId ? [
        { to: `/projects/${projectId}`, icon: Home, label: t('project.details'), end: true },
        { to: `/projects/${projectId}/scripts`, icon: FileText, label: t('nav.scripts') },
        { to: `/projects/${projectId}/chart`, icon: Clapperboard, label: t('nav.sceneChart') },
        { to: `/projects/${projectId}/cast`, icon: Users, label: t('nav.casting') },
        { to: `/projects/${projectId}/staff`, icon: Wrench, label: t('nav.staff') },
        { to: `/projects/${projectId}/schedule`, icon: Calendar, label: t('nav.schedule') },
        { to: `/projects/${projectId}/attendance`, icon: ClipboardCheck, label: t('nav.attendance') },
        { to: `/projects/${projectId}/settings`, icon: Settings, label: t('nav.settings') },
    ] : [];

    return (
        <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col border-r border-gray-800">
            <div className="h-16 flex items-center px-6 border-b border-gray-800">
                <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    PSC Web
                </span>
            </div>

            <nav className="flex-1 overflow-y-auto py-4">
                <div className="px-3 mb-2">
                    <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2 px-3">
                        Apps
                    </p>
                    <ul className="space-y-1">
                        {commonLinks.map((link) => (
                            <li key={link.to}>
                                <NavLink
                                    to={link.to}
                                    className={({ isActive }) =>
                                        cn(
                                            "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                                            isActive
                                                ? "bg-purple-500/10 text-purple-400"
                                                : "text-gray-400 hover:bg-gray-800 hover:text-white"
                                        )
                                    }
                                >
                                    <link.icon className="w-5 h-5" />
                                    {link.label}
                                </NavLink>
                            </li>
                        ))}
                    </ul>
                </div>

                {projectId && (
                    <div className="px-3 mt-6">
                        <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2 px-3">
                            Project
                        </p>
                        <ul className="space-y-1">
                            {projectLinks.map((link) => (
                                <li key={link.to}>
                                    <NavLink
                                        to={link.to}
                                        end={link.end}
                                        className={({ isActive }) =>
                                            cn(
                                                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                                                isActive
                                                    ? "bg-purple-500/10 text-purple-400"
                                                    : "text-gray-400 hover:bg-gray-800 hover:text-white"
                                            )
                                        }
                                    >
                                        <link.icon className="w-5 h-5" />
                                        {link.label}
                                    </NavLink>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </nav>

            {/* User Info at bottom - Discord Info */}
            {user && (
                <div className="p-4 border-t border-gray-800">
                    <div className="flex items-center gap-3">
                        {/* Discord Avatar */}
                        {user.discord_avatar_url ? (
                            <img
                                src={user.discord_avatar_url}
                                alt={user.screen_name || user.discord_id}
                                className="w-10 h-10 rounded-full ring-2 ring-purple-500"
                            />
                        ) : (
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg">
                                {(user.screen_name || user.discord_username || user.discord_id).charAt(0).toUpperCase()}
                            </div>
                        )}

                        {/* User Info */}
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-white truncate">
                                {user.screen_name || user.discord_username}
                            </p>
                            <p className="text-xs text-gray-400 truncate">
                                {user.discord_id}
                            </p>
                        </div>
                    </div>

                    {/* Logout Button */}
                    <button
                        onClick={() => {
                            // ログアウト処理
                            localStorage.removeItem('token');
                            window.location.href = '/login';
                        }}
                        className="mt-3 w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md transition-colors flex items-center justify-center gap-2"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                            <polyline points="16 17 21 12 16 7"></polyline>
                            <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                        {t('common.logout')}
                    </button>
                </div>
            )}
        </aside>
    );
}
