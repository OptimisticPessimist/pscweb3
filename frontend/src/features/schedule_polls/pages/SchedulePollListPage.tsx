import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { schedulePollApi } from '../api/schedulePoll';
import { Calendar, Clock, Plus, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHead } from '@/components/PageHead';

export const SchedulePollListPage: React.FC = () => {
    const { t } = useTranslation();
    const { projectId } = useParams<{ projectId: string }>();

    const { data: polls, isLoading } = useQuery({
        queryKey: ['schedulePolls', projectId],
        queryFn: () => schedulePollApi.getPolls(projectId!),
        enabled: !!projectId,
    });

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            <PageHead title={t('schedulePoll.listTitle') || '日程調整一覧'} />

            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">{t('schedulePoll.listTitle') || '日程調整一覧'}</h1>
                    <p className="text-sm text-gray-600">{t('schedulePoll.listDescription') || 'プロジェクトメンバーと稽古日程を調整します。'}</p>
                </div>
                <Link
                    to={`/projects/${projectId}/polls/create`}
                    className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors shadow-sm"
                >
                    <Plus className="h-5 w-5 mr-2" />
                    {t('schedulePoll.createButton') || '新しい日程調整'}
                </Link>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <div className="divide-y divide-gray-200">
                    {polls?.length === 0 ? (
                        <div className="p-12 text-center">
                            <Calendar className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900">{t('schedulePoll.noPolls') || '日程調整がありません'}</h3>
                            <p className="mt-1 text-sm text-gray-500">{t('schedulePoll.noPollsMessage') || '新しい日程調整を作成して、Discordで共有しましょう。'}</p>
                        </div>
                    ) : (
                        polls?.map((poll) => (
                            <Link
                                key={poll.id}
                                to={`/projects/${projectId}/polls/${poll.id}`}
                                className="block hover:bg-gray-50 transition-colors"
                            >
                                <div className="px-6 py-4 flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center">
                                            <h3 className="text-lg font-semibold text-indigo-600 truncate">
                                                {poll.title}
                                            </h3>
                                            {poll.is_closed && (
                                                <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                                                    {t('common.closed') || '完了'}
                                                </span>
                                            )}
                                        </div>
                                        <div className="mt-1 flex items-center text-sm text-gray-500 space-x-4">
                                            <div className="flex items-center">
                                                <Calendar className="h-4 w-4 mr-1" />
                                                <span>{poll.candidates.length} {t('schedulePoll.candidatesCount') || '件の候補日'}</span>
                                            </div>
                                            <div className="flex items-center">
                                                <Clock className="h-4 w-4 mr-1" />
                                                <span>{new Date(poll.created_at).toLocaleDateString()} {t('common.created') || '作成'}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <ChevronRight className="h-5 w-5 text-gray-400" />
                                </div>
                            </Link>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};
