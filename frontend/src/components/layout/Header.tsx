import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { useTranslation } from 'react-i18next';

export function Header() {
    const location = useLocation();
    const { t } = useTranslation();
    const pathnames = location.pathname.split('/').filter((x) => x);

    // パンくずリスト生成
    const breadcrumbItems = [
        { name: t('nav.dashboard'), path: '/dashboard' },
    ];

    // パスからパンくずリストを構築
    let currentPath = '';
    pathnames.forEach((segment, index) => {
        currentPath += `/${segment}`;

        // 翻訳キーに基づいた名前にマッピング
        let name = segment;
        if (segment === 'projects') name = t('nav.projects');
        else if (segment === 'scripts') name = t('nav.scripts');
        else if (segment === 'casting') name = t('nav.casting');
        else if (segment === 'staff') name = t('nav.staff');
        else if (segment === 'schedule') name = t('nav.schedule');
        else if (segment === 'attendance') name = t('nav.attendance');
        else if (segment === 'scene-charts') name = t('nav.sceneChart');
        else if (segment === 'settings') name = t('nav.settings');
        else if (segment === 'my-schedule') name = t('nav.mySchedule');
        // プロジェクトIDやその他のIDは数値の場合そのまま、詳細ページは"Details"等
        else if (/^[0-9a-f-]+$/i.test(segment)) {
            // UUIDやIDの場合は表示しない（次のセグメントで判断）
            return;
        }

        breadcrumbItems.push({
            name: name,  // 翻訳済みの名前をそのまま使用
            path: currentPath
        });
    });

    return (
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
            {/* Left: Breadcrumb */}
            <nav className="flex items-center gap-2 text-sm">
                <Link
                    to="/dashboard"
                    className="text-gray-500 hover:text-gray-700 transition-colors"
                >
                    <Home className="w-4 h-4" />
                </Link>

                {breadcrumbItems.slice(1).map((item) => {
                    const isLast = item.path === breadcrumbItems[breadcrumbItems.length - 1].path;
                    return (
                        <div key={item.path} className="flex items-center gap-2">
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                            {isLast ? (
                                <span className="font-medium text-gray-900">{item.name}</span>
                            ) : (
                                <Link
                                    to={item.path}
                                    className="text-gray-500 hover:text-gray-700 transition-colors"
                                >
                                    {item.name}
                                </Link>
                            )}
                        </div>
                    );
                })}
            </nav>

            {/* Right: Language Switcher */}
            <div className="flex items-center">
                <LanguageSwitcher />
            </div>
        </header>
    );
}
