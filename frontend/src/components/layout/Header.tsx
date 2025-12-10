import { Breadcrumbs } from '../Breadcrumbs';
import { Menu } from 'lucide-react';

export function Header() {
    return (
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
            <div className="flex items-center gap-4">
                {/* モバイル用メニューボタン（今回は機能なし） */}
                <button className="lg:hidden p-1 rounded-md hover:bg-gray-100">
                    <Menu className="w-6 h-6 text-gray-600" />
                </button>

                <Breadcrumbs />
            </div>

            {/* 右側の検索・通知エリアは不要なため削除 */}
            <div className="flex items-center gap-4">
                {/* 必要に応じて将来的に機能を追加 */}
            </div>
        </header>
    );
}
