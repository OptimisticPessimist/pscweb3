import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { reservationsApi } from '../api';
import { PageHead } from '@/components/PageHead';

interface CancelForm {
    reservation_id: string;
    email: string;
}

export const ReservationCancelPage = () => {
    const { t } = useTranslation();
    const { register, handleSubmit, reset, formState: { errors } } = useForm<CancelForm>();

    const cancelMutation = useMutation({
        mutationFn: reservationsApi.cancelReservation,
        onSuccess: () => {
            toast.success(t('reservation.cancel.success', 'Reservation cancelled successfully.'));
            reset();
        },
        onError: (error: any) => {
            const msg = error.response?.data?.detail || t('common.error');
            toast.error(msg);
        }
    });

    const onSubmit = (data: CancelForm) => {
        if (confirm(t('reservation.cancel.confirm', 'Are you sure you want to cancel this reservation?'))) {
            cancelMutation.mutate(data);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
            <PageHead title={t('reservation.cancel.title', 'Cancel Reservation')} />
            <div className="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden md:max-w-xl p-8">
                <div className="text-center mb-8">
                    <h2 className="text-2xl font-bold text-gray-900">
                        {t('reservation.cancel.title', 'Cancel Reservation')}
                    </h2>
                    <p className="mt-2 text-sm text-gray-500">
                        {t('reservation.cancel.description', 'Please enter your Reservation ID and Email to cancel.')}
                    </p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            {t('reservation.cancel.reservationId', 'Reservation ID')}
                        </label>
                        <input
                            type="text"
                            {...register('reservation_id', { required: true })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm p-2 border"
                            placeholder="UUID"
                        />
                        {errors.reservation_id && <p className="text-red-500 text-sm mt-1">{t('common.required')}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            {t('reservation.form.email')}
                        </label>
                        <input
                            type="email"
                            {...register('email', { required: true })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm p-2 border"
                            placeholder="example@email.com"
                        />
                        {errors.email && <p className="text-red-500 text-sm mt-1">{t('common.required')}</p>}
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={cancelMutation.isPending}
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
                        >
                            {cancelMutation.isPending ? t('common.processing') : t('reservation.cancel.submit', 'Cancel Reservation')}
                        </button>
                    </div>
                </form>

                <div className="mt-6 text-center">
                    <Link to="/schedule" className="text-sm text-indigo-600 hover:text-indigo-500">
                        {t('common.back', 'Back to Schedule')}
                    </Link>
                </div>
            </div>
        </div>
    );
};
