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
    CalendarDays
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// tailwind-merge helper
function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

export function Sidebar() {
    const { projectId } = useParams<{ projectId: string }>();

    // プロジェクト選択中かどうかでメニューを切り替える
    // 共通メニュー
    const commonLinks = [
        { to: '/', icon: LayoutGrid, label: 'Dashboard' },
        { to: '/my-schedule', icon: CalendarDays, label: 'My Schedule' },
    ];


    // プロジェクト内メニュー
    const projectLinks = projectId ? [
        { to: `/projects/${projectId}`, icon: Home, label: 'Overview', end: true },
        { to: `/projects/${projectId}/scripts`, icon: FileText, label: 'Scripts' },
        { to: `/projects/${projectId}/chart`, icon: Clapperboard, label: 'Scene Chart' },
        { to: `/projects/${projectId}/cast`, icon: Users, label: 'Cast' },
        { to: `/projects/${projectId}/staff`, icon: Wrench, label: 'Staff' },
        { to: `/projects/${projectId}/schedule`, icon: Calendar, label: 'Schedule' },
        { to: `/projects/${projectId}/settings`, icon: Settings, label: 'Settings' },
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

            <div className="p-4 border-t border-gray-800">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                        <span className="text-xs font-bold">U</span>
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">User Name</p>
                        <p className="text-xs text-gray-500 truncate">user@example.com</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
