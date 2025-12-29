import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { reservationsApi } from '../api';
import { PageHead } from '@/components/PageHead';

export const PublicSchedulePage = () => {
    const { t } = useTranslation();

    const { data: milestones, isLoading } = useQuery({
        queryKey: ['publicSchedule'],
        queryFn: reservationsApi.getPublicSchedule
    });

    if (isLoading) return <div className="flex justify-center p-10">{t('common.loading')}</div>;

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
            <PageHead title={t('schedule.public.title', 'Ticket Schedule')} />
            <div className="max-w-4xl mx-auto">
                <div className="text-center mb-10">
                    <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                        {t('schedule.public.headline', 'Upcoming Performances')}
                    </h1>
                    <p className="mt-3 text-xl text-gray-500">
                        {t('schedule.public.subheadline', 'Check out our schedule and book your tickets.')}
                    </p>
                    {/* 🆕 ビュー切替ボタン */}
                    <div className="mt-4 flex justify-center gap-2">
                        <span className="inline-flex px-3 py-2 text-sm font-medium text-indigo-600 bg-white border border-indigo-600 rounded-md">
                            📋 リスト
                        </span>
                        <a
                            href="/schedule/calendar"
                            className="inline-flex px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                        >
                            📅 カレンダー
                        </a>
                    </div>
                </div>

                <div className="space-y-6">
                    {milestones?.length === 0 ? (
                        <div className="text-center text-gray-500 py-10">
                            {t('schedule.public.noEvents', 'No upcoming events found.')}
                        </div>
                    ) : (
                        milestones?.map((milestone) => (
                            <div key={milestone.id} className="bg-white shadow rounded-lg overflow-hidden flex flex-col md:flex-row hover:shadow-lg transition-shadow duration-300">
                                <div className="p-6 flex-1">
                                    <div className="text-sm font-medium text-indigo-600 mb-1">
                                        {milestone.project_name}
                                    </div>
                                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                                        {milestone.title}
                                    </h3>
                                    <div className="text-gray-500 flex flex-col space-y-1 mb-4">
                                        <div className="flex items-center">
                                            <span className="mr-2">📅</span>
                                            {format(new Date(milestone.start_date), 'yyyy/MM/dd (EEE) HH:mm', { locale: ja })}
                                            {milestone.end_date && ` - ${format(new Date(milestone.end_date), 'HH:mm')}`}
                                        </div>
                                        {milestone.location && (
                                            <div className="flex items-center">
                                                <span className="mr-2">📍</span>
                                                {milestone.location}
                                            </div>
                                        )}
                                    </div>

                                    {milestone.reservation_capacity && (
                                        <div className="text-sm text-gray-400">
                                            Capacity: {milestone.reservation_capacity}
                                        </div>
                                    )}
                                </div>
                                <div className="bg-gray-50 px-6 py-4 md:py-0 md:px-6 md:w-48 flex items-center justify-center border-t md:border-t-0 md:border-l border-gray-100">
                                    <Link
                                        to={`/reservations/${milestone.id}`}
                                        className="w-full text-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                                    >
                                        {t('schedule.public.bookNow', 'Reserve Ticket')}
                                    </Link>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <div className="mt-12 text-center">
                    <Link to="/reservations/cancel" className="text-sm text-gray-500 hover:text-gray-900 hover:underline">
                        {t('reservation.cancel.linkText', 'Need to cancel a reservation?')}
                    </Link>
                </div>
            </div>
        </div>
    );
};
