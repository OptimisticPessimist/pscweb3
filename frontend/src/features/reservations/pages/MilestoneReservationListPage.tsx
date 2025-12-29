import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

import { reservationsApi } from '../api';
import { projectsApi } from '@/features/projects/api/projects';
import { Loading } from '@/components/Loading';

export const MilestoneReservationListPage = () => {
    const { t } = useTranslation();
    const { projectId, milestoneId } = useParams<{ projectId: string; milestoneId: string }>();
    const queryClient = useQueryClient();

    const { data: milestones, isLoading: milestonesLoading } = useQuery({
        queryKey: ['project-milestones', projectId],
        queryFn: () => projectsApi.getMilestones(projectId!),
        enabled: !!projectId
    });

    const milestone = milestones?.find((m) => m.id === milestoneId);
    const milestoneLoading = milestonesLoading;

    const { data: reservations = [], isLoading: reservationsLoading } = useQuery({
        queryKey: ['milestone-reservations', milestoneId],
        queryFn: () => reservationsApi.getMilestoneReservations(milestoneId!),
        enabled: !!milestoneId
    });

    const updateMutation = useMutation({
        mutationFn: (data: { id: string; attended: boolean }) =>
            reservationsApi.updateAttendance(data.id, data.attended),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['milestone-reservations', milestoneId] });
            toast.success(t('reservation.milestone.updateSuccess'));
        },
        onError: () => {
            toast.error(t('reservation.milestone.updateError'));
        }
    });

    if (milestoneLoading || reservationsLoading) return <Loading />;
    if (!milestone) return <div className="text-center py-10 text-red-500">{t('reservation.milestone.notFound')}</div>;

    const totalCount = reservations.reduce((sum, r) => sum + r.count, 0);

    return (
        <div className="space-y-6">
            {/* ヘッダー */}
            <div className="bg-white shadow sm:rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="flex-1">
                            <h1 className="text-2xl font-bold text-gray-900">{milestone.title}</h1>
                            <div className="mt-2 text-sm text-gray-500 space-y-1">
                                <p>📅 {format(new Date(milestone.start_date), 'yyyy/MM/dd HH:mm')}</p>
                                {milestone.location && <p>📍 {milestone.location}</p>}
                                <p className="text-lg font-semibold text-indigo-600 mt-2">
                                    {t('reservation.milestone.totalReservations', { count: totalCount, items: reservations.length })}
                                </p>
                            </div>
                        </div>
                        <Link
                            to={`/projects/${projectId}`}
                            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        >
                            {t('reservation.milestone.backToProject')}
                        </Link>
                    </div>
                </div>
            </div>

            {/* 予約者リスト */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 bg-gray-50 border-b border-gray-200">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                        {t('reservation.milestone.reservationList')}
                    </h3>
                </div>
                <ul role="list" className="divide-y divide-gray-200">
                    {reservations.map((reservation) => (
                        <li key={reservation.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center space-x-3">
                                        <p className={`text-sm font-medium truncate ${reservation.attended ? 'text-gray-500 line-through' : 'text-indigo-600'}`}>
                                            {reservation.name}
                                        </p>
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                            {t('reservation.form.sheets', { count: reservation.count })}
                                        </span>
                                    </div>
                                    <div className="mt-2 flex">
                                        <div className="flex items-center text-sm text-gray-500">
                                            <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                            </svg>
                                            <p className="truncate">{reservation.email}</p>
                                        </div>
                                    </div>
                                    {reservation.referral_name && (
                                        <div className="mt-1 text-xs text-gray-400">
                                            {t('reservation.milestone.referralBy', { name: reservation.referral_name })}
                                        </div>
                                    )}
                                </div>
                                <div className="ml-4 flex-shrink-0 flex flex-col items-end space-y-2">
                                    <p className="text-xs text-gray-400">
                                        {t('reservation.milestone.reservedAt', { date: format(new Date(reservation.created_at), 'MM/dd HH:mm') })}
                                    </p>
                                    <button
                                        onClick={() => updateMutation.mutate({
                                            id: reservation.id,
                                            attended: !reservation.attended
                                        })}
                                        disabled={updateMutation.isPending}
                                        className={`relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${reservation.attended ? 'bg-green-600' : 'bg-gray-200'}`}
                                    >
                                        <span className="sr-only">Use setting</span>
                                        <span
                                            aria-hidden="true"
                                            className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200 ${reservation.attended ? 'translate-x-5' : 'translate-x-0'}`}
                                        />
                                    </button>
                                    <span className="text-xs text-gray-500">
                                        {reservation.attended ? t('reservation.admin.attended') : t('reservation.admin.unattended')}
                                    </span>
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            {reservations.length === 0 && (
                <div className="text-center py-10 text-gray-500">
                    {t('reservation.admin.noReservations')}
                </div>
            )}
        </div>
    );
};
