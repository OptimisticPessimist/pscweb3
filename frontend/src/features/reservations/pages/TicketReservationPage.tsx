import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

import { reservationsApi } from '../api';
import type { ReservationCreateRequest } from '../types';
// Checking existing typical structure... usually in components/ui or similar.
// I will check for UI components first or use basic HTML to be safe then refactor if needed.
// Actually checking list_dir earlier: components/ has Loading and generic stuff.
// I should use standard HTML + Tailwind classes to match 'Rich Aesthetics'.

import { PageHead } from '@/components/PageHead';

export const TicketReservationPage = () => {
    const { milestoneId } = useParams<{ milestoneId: string }>();
    const navigate = useNavigate();
    const { t } = useTranslation();
    const [roleFilter, setRoleFilter] = useState<'all' | 'cast'>('cast');

    const { data: milestone, isLoading: isMilestoneLoading, error: milestoneError } = useQuery({
        queryKey: ['publicMilestone', milestoneId],
        queryFn: () => reservationsApi.getMilestone(milestoneId!),
        enabled: !!milestoneId
    });

    const { data: members = [] } = useQuery({
        queryKey: ['publicProjectMembers', milestone?.project_id, roleFilter],
        queryFn: () => reservationsApi.getProjectMembers(milestone!.project_id, roleFilter === 'all' ? undefined : roleFilter),
        enabled: !!milestone?.project_id
    });

    const { register, handleSubmit, formState: { errors } } = useForm<ReservationCreateRequest>();

    const createMutation = useMutation({
        mutationFn: reservationsApi.createReservation,
        onSuccess: (data) => {
            navigate('/reservations/completed', { state: { reservation: data, milestone } });
        },
        onError: (error: any) => {
            const msg = error.response?.data?.detail || t('common.error');
            toast.error(msg);
        }
    });

    const onSubmit = (data: ReservationCreateRequest) => {
        if (!milestoneId) return;
        createMutation.mutate({
            ...data,
            milestone_id: milestoneId,
            count: Number(data.count) // ensure number
        });
    };

    if (isMilestoneLoading) return <div className="flex justify-center p-10">{t('common.loading')}</div>;
    if (milestoneError || !milestone) return <div className="text-center p-10 text-red-500">{t('project.notFound')}</div>; // Assuming generic not found or publicScript.noScripts

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
            <PageHead title={t('reservation.form.title')} />
            <div className="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden md:max-w-2xl">
                <div className="md:flex-col">
                    <div className="p-8 bg-indigo-600 text-white">
                        <div className="uppercase tracking-wide text-sm font-semibold opacity-80">{t('reservation.form.title')}</div>
                        {milestone.project_name && (
                            <p className="mt-2 text-lg font-medium opacity-90">{milestone.project_name}</p>
                        )}
                        <h1 className="block mt-1 text-2xl leading-tight font-bold">{milestone.title}</h1>
                        <p className="mt-2 opacity-90">
                            {format(new Date(milestone.start_date), 'yyyy/MM/dd (EEE) HH:mm', { locale: ja })}
                        </p>
                        {milestone.location && <p className="mt-1 text-sm opacity-80">@{milestone.location}</p>}
                        {milestone.reservation_capacity && (
                            <p className="mt-2 text-xs border border-white/30 inline-block px-2 py-1 rounded">
                                {t('project.settings.milestones.form.reservationCapacity').replace('(空欄で無制限)', '')}: {milestone.reservation_capacity}
                            </p>
                        )}
                    </div>

                    <div className="p-8">
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                            <div>
                                <label className="block text-sm font-medium text-gray-700">{t('reservation.form.name')} <span className="text-red-500">*</span></label>
                                <input
                                    type="text"
                                    {...register('name', { required: t('project.nameRequired') })}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                    placeholder={t('dashboard.noDescription')} // Placeholder reuse or empty
                                />
                                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">{t('reservation.form.email')} <span className="text-red-500">*</span></label>
                                <input
                                    type="email"
                                    {...register('email', { required: true })}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                    placeholder="example@email.com"
                                />
                                {errors.email && <p className="text-red-500 text-sm mt-1">{t('common.error')}</p>}
                            </div>


                            <div>
                                <label className="block text-sm font-medium text-gray-700">{t('reservation.form.count')} <span className="text-red-500">*</span></label>
                                <select
                                    {...register('count', { required: true })}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                >
                                    {(() => {
                                        const capacity = milestone?.reservation_capacity;
                                        const currentCount = milestone?.current_reservation_count || 0;
                                        const available = capacity ? Math.max(0, capacity - currentCount) : 4;
                                        const maxSelectable = Math.min(4, available);

                                        if (maxSelectable === 0) {
                                            return <option value="">満席です</option>;
                                        }

                                        return Array.from({ length: maxSelectable }, (_, i) => i + 1).map(n => (
                                            <option key={n} value={n}>{n}{t('reservation.form.sheets')}</option>
                                        ));
                                    })()}
                                </select>
                                {milestone?.reservation_capacity && (
                                    <div className="mt-1 space-y-1">
                                        <p className="text-xs text-gray-500">
                                            残り {Math.max(0, milestone.reservation_capacity - (milestone.current_reservation_count || 0))} 枚
                                        </p>
                                        <p className="text-xs text-amber-600">
                                            ※ 残り枚数は目安です。確定は送信時に行われます。
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div>
                                <div className="flex justify-between items-center">
                                    <label className="block text-sm font-medium text-gray-700">{t('reservation.form.referral')}</label>
                                    <div className="text-xs space-x-2">
                                        <button
                                            type="button"
                                            onClick={() => setRoleFilter('cast')}
                                            className={`px-2 py-0.5 rounded ${roleFilter === 'cast' ? 'bg-gray-200 font-bold' : 'text-gray-500'}`}
                                        >
                                            {t('reservation.form.roleFilter.cast')}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setRoleFilter('all')}
                                            className={`px-2 py-0.5 rounded ${roleFilter === 'all' ? 'bg-gray-200 font-bold' : 'text-gray-500'}`}
                                        >
                                            {t('reservation.form.roleFilter.all')}
                                        </button>
                                    </div>
                                </div>
                                <select
                                    {...register('referral_user_id')}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                >
                                    <option value="">{t('reservation.form.referralPlaceholder')}</option>
                                    {members.map(m => (
                                        <option key={m.id} value={m.id}>{m.name}</option>
                                    ))}
                                </select>
                                <p className="text-xs text-gray-500 mt-1">
                                    {t('reservation.form.referralHelp')}
                                </p>
                            </div>

                            <div className="pt-4">
                                <button
                                    type="submit"
                                    disabled={createMutation.isPending}
                                    className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                                >
                                    {createMutation.isPending ? t('reservation.form.submitting') : t('reservation.form.submit')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            <div className="text-center mt-8 text-gray-400 text-sm">
                Powered by PSC Web
            </div>
        </div>
    );
};
