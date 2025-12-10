import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from './api/projects';
import { scriptsApi } from '../scripts/api/scripts';
import { dashboardApi, type DashboardResponse } from '../dashboard/api/dashboard';
import { AlertCircle, Calendar, Clock, MapPin } from 'lucide-react';

export const ProjectDetailsPage = () => {
    const { projectId } = useParams<{ projectId: string }>();

    const { data: project, isLoading: isProjectLoading, error: projectError } = useQuery({
        queryKey: ['projects', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    const { data: scripts, isLoading: isScriptsLoading } = useQuery({
        queryKey: ['scripts', projectId],
        queryFn: () => scriptsApi.getScripts(projectId!),
        enabled: !!projectId,
    });

    const { data: dashboard } = useQuery({
        queryKey: ['dashboard', projectId],
        queryFn: () => dashboardApi.getDashboard(projectId!),
        enabled: !!projectId,
    });

    if (isProjectLoading) {
        return (
            <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (projectError || !project) {
        return (
            <div className="flex flex-col items-center justify-center h-full">
                <h2 className="text-xl font-bold text-gray-900">Project not found</h2>
                <Link to="/dashboard" className="text-indigo-600 hover:text-indigo-500 mt-4">
                    Return to Dashboard
                </Link>
            </div>
        );
    }

    const currentScript = scripts && scripts.length > 0 ? scripts[0] : null;

    // 重要アラートの計算
    const alerts = [];

    // 未回答の出欠確認
    if (dashboard && dashboard.pending_attendance_count > 0) {
        alerts.push({
            type: 'error',
            icon: AlertCircle,
            message: `未回答の出欠確認が${dashboard.pending_attendance_count}件あります`,
            link: `/projects/${projectId}/schedule`,  // Scheduleページに遷移
        });
    }

    // 直近の稽古（24時間以内）
    if (dashboard?.next_rehearsal) {
        const startTime = new Date(dashboard.next_rehearsal.start_time);
        const now = new Date();
        const hoursUntil = (startTime.getTime() - now.getTime()) / (1000 * 60 * 60);

        if (hoursUntil > 0 && hoursUntil <= 24) {
            alerts.push({
                type: 'warning',
                icon: Clock,
                message: `稽古が${Math.floor(hoursUntil)}時間後に開始されます`,
                link: `/projects/${projectId}/schedule`,
            });
        }
    }

    // 期限間近のマイルストーン（7日以内）
    if (dashboard?.next_milestone && dashboard.next_milestone.days_until <= 7) {
        alerts.push({
            type: 'info',
            icon: Calendar,
            message: `マイルストーン「${dashboard.next_milestone.title}」まで残り${dashboard.next_milestone.days_until}日`,
            link: `/projects/${projectId}/schedule`,
        });
    }

    return (
        <div className="p-6 space-y-6">
            {/* プロジェクト基本情報 */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h2>
                <div className="text-sm text-gray-500 space-y-1">
                    <p>Created: {new Date(project.created_at).toLocaleDateString()}</p>
                    <p>Role: <span className="capitalize">{project.role}</span></p>
                </div>
                <div className="mt-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Description</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">
                        {project.description || 'No description provided.'}
                    </p>
                </div>
            </div>

            {/* 重要アラート */}
            {alerts.length > 0 && (
                <div className="space-y-3">
                    {alerts.map((alert, index) => {
                        const Icon = alert.icon;
                        const bgColor = alert.type === 'error' ? 'bg-red-50 border-red-200' :
                            alert.type === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                                'bg-blue-50 border-blue-200';
                        const textColor = alert.type === 'error' ? 'text-red-800' :
                            alert.type === 'warning' ? 'text-yellow-800' :
                                'text-blue-800';
                        const iconColor = alert.type === 'error' ? 'text-red-500' :
                            alert.type === 'warning' ? 'text-yellow-500' :
                                'text-blue-500';

                        return (
                            <Link
                                key={index}
                                to={alert.link}
                                className={`block ${bgColor} border-l-4 p-4 rounded ${textColor} hover:opacity-80 transition-opacity`}
                            >
                                <div className="flex items-center">
                                    <Icon className={`h-5 w-5 ${iconColor} mr-3`} />
                                    <p className="font-medium">{alert.message}</p>
                                </div>
                            </Link>
                        );
                    })}
                </div>
            )}

            {/* クイック統計 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 次回稽古カード */}
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-purple-500">
                    <div className="flex justify-between items-start">
                        <h3 className="font-semibold text-gray-900">次回稽古</h3>
                        <Link to={`/projects/${projectId}/schedule`} className="text-xs text-indigo-600 hover:text-indigo-500">
                            View Schedule
                        </Link>
                    </div>
                    {dashboard?.next_rehearsal ? (
                        <div className="mt-3 space-y-2">
                            <p className="text-lg font-medium text-gray-900">{dashboard.next_rehearsal.title}</p>
                            <div className="flex items-center text-sm text-gray-600">
                                <Clock className="h-4 w-4 mr-2" />
                                {new Date(dashboard.next_rehearsal.start_time).toLocaleString('ja-JP', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </div>
                            {dashboard.next_rehearsal.location && (
                                <div className="flex items-center text-sm text-gray-600">
                                    <MapPin className="h-4 w-4 mr-2" />
                                    {dashboard.next_rehearsal.location}
                                </div>
                            )}
                        </div>
                    ) : (
                        <p className="mt-3 text-gray-400">予定なし</p>
                    )}
                </div>

                {/* 次のマイルストーンカード */}
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-pink-500">
                    <div className="flex justify-between items-start">
                        <h3 className="font-semibold text-gray-900">次のマイルストーン</h3>
                        <Link to={`/projects/${projectId}/schedule`} className="text-xs text-indigo-600 hover:text-indigo-500">
                            View Schedule
                        </Link>
                    </div>
                    {dashboard?.next_milestone ? (
                        <div className="mt-3 space-y-2">
                            <p className="text-lg font-medium text-gray-900">{dashboard.next_milestone.title}</p>
                            <div className="flex items-center text-sm text-gray-600">
                                <Calendar className="h-4 w-4 mr-2" />
                                {new Date(dashboard.next_milestone.start_date).toLocaleDateString('ja-JP', {
                                    month: 'short',
                                    day: 'numeric'
                                })}
                            </div>
                            <div className="flex items-center">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${dashboard.next_milestone.days_until <= 7 ? 'bg-red-100 text-red-800' :
                                    dashboard.next_milestone.days_until <= 14 ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-green-100 text-green-800'
                                    }`}>
                                    残り{dashboard.next_milestone.days_until}日
                                </span>
                            </div>
                        </div>
                    ) : (
                        <p className="mt-3 text-gray-400">予定なし</p>
                    )}
                </div>

                {/* Current Script */}
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-indigo-500">
                    <div className="flex justify-between items-start">
                        <h3 className="font-semibold text-gray-900">Current Script</h3>
                        <Link to={`/projects/${projectId}/scripts`} className="text-xs text-indigo-600 hover:text-indigo-500">
                            {currentScript ? 'Update' : 'Upload'}
                        </Link>
                    </div>
                    {isScriptsLoading ? (
                        <p className="mt-2 text-sm text-gray-500">Loading...</p>
                    ) : currentScript ? (
                        <div className="mt-2">
                            <div className="flex items-baseline space-x-2">
                                <p className="text-lg font-medium text-gray-900 truncate" title={currentScript.title}>
                                    {currentScript.title}
                                </p>
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                    Rev.{currentScript.revision}
                                </span>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                                {new Date(currentScript.uploaded_at).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </p>
                        </div>
                    ) : (
                        <div className="mt-2 text-gray-500">
                            <p className="text-lg font-medium text-gray-400">No script</p>
                            <p className="text-xs mt-1">Ready to upload</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
