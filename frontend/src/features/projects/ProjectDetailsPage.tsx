import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from './api/projects';
import { scriptsApi } from '../scripts/api/scripts';
import { dashboardApi, type DashboardResponse } from '../dashboard/api/dashboard';
import { AlertCircle, Calendar, Clock, MapPin } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ProjectDetailsPage = () => {
    const { t, i18n } = useTranslation();
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
                <h2 className="text-xl font-bold text-gray-900">{t('project.notFound')}</h2>
                <Link to="/dashboard" className="text-indigo-600 hover:text-indigo-500 mt-4">
                    {t('project.returnToDashboard')}
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
            message: t('project.pendingAttendance', { count: dashboard.pending_attendance_count }),
            link: `/projects/${projectId}/attendance`,
        });
    }

    // 直近の稽古（24時間以内）
    if (dashboard?.next_rehearsal) {
        const startTime = new Date(dashboard.next_rehearsal.start_time);
        const now = new Date();
        const hoursUntil = (startTime.getTime() - now.getTime()) / (1000 * 60 * 60);


        if (hoursUntil > 0 && hoursUntil <= 24) {
            const hours = Math.floor(hoursUntil);
            const message = t('project.rehearsalInHours', { hours });
            console.log('[DEBUG] Rehearsal alert:', {
                hours,
                message,
                language: i18n.language,
                rawKey: 'project.rehearsalInHours',
                exists: i18n.exists('project.rehearsalInHours')
            });
            alerts.push({
                type: 'warning',
                icon: Clock,
                message,
                link: `/projects/${projectId}/schedule`,
            });
        }
    }

    // 期限間近のマイルストーン（7日以内）
    if (dashboard?.next_milestone && dashboard.next_milestone.days_until <= 7) {
        alerts.push({
            type: 'info',
            icon: Calendar,
            message: t('project.milestoneInDays', { title: dashboard.next_milestone.title, days: dashboard.next_milestone.days_until }),
            link: `/projects/${projectId}/schedule`,
        });
    }

    return (
        <div className="p-6 space-y-6">
            {/* プロジェクト基本情報 */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h2>
                <div className="text-sm text-gray-500 space-y-1">
                    <p>{t('project.created')}: {new Date(project.created_at).toLocaleDateString(i18n.language)}</p>
                    <p>{t('project.role')}: <span className="capitalize">{project.role}</span></p>
                </div>
                <div className="mt-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">{t('project.description')}</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">
                        {project.description || t('project.noDescription')}
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
                        <h3 className="font-semibold text-gray-900">{t('project.nextRehearsal')}</h3>
                        <Link to={`/projects/${projectId}/schedule`} className="text-xs text-indigo-600 hover:text-indigo-500">
                            {t('project.viewSchedule')}
                        </Link>
                    </div>
                    {dashboard?.next_rehearsal ? (
                        <div className="mt-3 space-y-2">
                            <p className="text-lg font-medium text-gray-900">{dashboard.next_rehearsal.title}</p>
                            <div className="flex items-center text-sm text-gray-600">
                                <Clock className="h-4 w-4 mr-2" />
                                {new Date(dashboard.next_rehearsal.start_time).toLocaleString(i18n.language, {
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
                        <p className="mt-3 text-gray-400">{t('project.noSchedule')}</p>
                    )}
                </div>

                {/* 次のマイルストーンカード */}
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-pink-500">
                    <div className="flex justify-between items-start">
                        <h3 className="font-semibold text-gray-900">{t('project.nextMilestone')}</h3>
                        <Link to={`/projects/${projectId}/schedule`} className="text-xs text-indigo-600 hover:text-indigo-500">
                            {t('project.viewSchedule')}
                        </Link>
                    </div>
                    {dashboard?.next_milestone ? (
                        <div className="mt-3 space-y-2">
                            <p className="text-lg font-medium text-gray-900">{dashboard.next_milestone.title}</p>
                            <div className="flex items-center text-sm text-gray-600">
                                <Calendar className="h-4 w-4 mr-2" />
                                {new Date(dashboard.next_milestone.start_date).toLocaleDateString(i18n.language, {
                                    month: 'short',
                                    day: 'numeric'
                                })}
                            </div>
                            <div className="flex items-center">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${dashboard.next_milestone.days_until <= 7 ? 'bg-red-100 text-red-800' :
                                    dashboard.next_milestone.days_until <= 14 ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-green-100 text-green-800'
                                    }`}>
                                    {t('project.daysRemaining', { days: dashboard.next_milestone.days_until })}
                                </span>
                            </div>
                        </div>
                    ) : (
                        <p className="mt-3 text-gray-400">{t('project.noSchedule')}</p>
                    )}
                </div>

                {/* Current Script */}
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-indigo-500">
                    <div className="flex justify-between items-start">
                        <h3 className="font-semibold text-gray-900">{t('project.currentScript')}</h3>
                        <Link to={`/projects/${projectId}/scripts`} className="text-xs text-indigo-600 hover:text-indigo-500">
                            {currentScript ? t('project.update') : t('script.upload')}
                        </Link>
                    </div>
                    {isScriptsLoading ? (
                        <p className="mt-2 text-sm text-gray-500">{t('common.loading')}</p>
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
                                {new Date(currentScript.uploaded_at).toLocaleString(i18n.language, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </p>
                        </div>
                    ) : (
                        <div className="mt-2 text-gray-500">
                            <p className="text-lg font-medium text-gray-400">{t('project.noScript')}</p>
                            <p className="text-xs mt-1">{t('project.readyToUpload')}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
