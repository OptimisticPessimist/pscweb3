import { useLocation } from 'react-router-dom';
import { Bell, Search, Menu } from 'lucide-react';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

export function Header() {
    const location = useLocation();
    const pathnames = location.pathname.split('/').filter((x) => x);

    // 簡易的なパンくずリスト生成（今回は表示のみで機能はしない）
    const breadcrumbs = pathnames.length > 0 ? pathnames.join(' / ') : 'Dashboard';

    return (
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
            <div className="flex items-center gap-4">
                {/* モバイル用メニューボタン（今回は機能なし） */}
                <button className="lg:hidden p-1 rounded-md hover:bg-gray-100">
                    <Menu className="w-6 h-6 text-gray-600" />
                </button>

                <h2 className="text-lg font-semibold text-gray-800 capitalize">
                    {breadcrumbs}
                </h2>
            </div>

            <div className="flex items-center gap-4">
                <div className="relative">
                    <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                        type="text"
                        placeholder="Search..."
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent w-64"
                    />
                </div>

                <button className="p-2 rounded-full hover:bg-gray-100 relative">
                    <Bell className="w-5 h-5 text-gray-600" />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
                </button>

                <LanguageSwitcher />
            </div>
        </header>
    );
}
