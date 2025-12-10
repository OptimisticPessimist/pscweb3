import { Link, useLocation, useParams } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/features/projects/api/projects';

const ROUTE_LABELS: Record<string, string> = {
    dashboard: 'Dashboard',
    'my-schedule': 'My Schedule',
    projects: 'Projects',
    scripts: 'Scripts',
    chart: 'Scene Chart',
    cast: 'Cast',
    staff: 'Staff',
    schedule: 'Schedule',
    attendance: 'Attendance',
    settings: 'Settings',
    upload: 'Upload',
};

export function Breadcrumbs() {
    const location = useLocation();
    const { projectId } = useParams<{ projectId: string }>();

    // プロジェクト名を取得
    const { data: project } = useQuery({
        queryKey: ['projects', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
        staleTime: 1000 * 60 * 5, // キャッシュ有効期間: 5分
    });

    const pathnames = location.pathname.split('/').filter((x) => x);

    const items = pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;

        let label = ROUTE_LABELS[value] || value;

        // プロジェクトIDの場合はプロジェクト名を表示
        if (value === projectId) {
            label = project?.name || 'Project';
        }

        // 短いID表示へのフォールバック（例：スクリプトIDなど）
        // 32文字以上のUUIDなら短縮表示などを検討しても良いが、今回はそのまま

        return { label, to, isLast };
    });

    return (
        <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2">
                <li>
                    <div className="flex items-center">
                        <Link to="/dashboard" className="text-gray-400 hover:text-gray-500">
                            <Home className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                            <span className="sr-only">Dashboard</span>
                        </Link>
                    </div>
                </li>

                {items.map((item) => {
                    // Dashboardセグメントはホームアイコンと重複するのでスキップ
                    if (item.label === 'Dashboard') return null;

                    return (
                        <li key={item.to}>
                            <div className="flex items-center">
                                <ChevronRight className="h-5 w-5 flex-shrink-0 text-gray-400" aria-hidden="true" />
                                {item.isLast ? (
                                    <span className="ml-2 text-sm font-medium text-gray-500">{item.label}</span>
                                ) : (
                                    <Link
                                        to={item.to}
                                        className="ml-2 text-sm font-medium text-gray-500 hover:text-gray-700"
                                    >
                                        {item.label}
                                    </Link>
                                )}
                            </div>
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
}
