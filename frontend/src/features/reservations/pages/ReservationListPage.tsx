import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { toast } from 'react-hot-toast';

import { reservationsApi } from '../api';
import type { ReservationResponse } from '../types';
import { Loading } from '@/components/Loading';

export const ReservationListPage = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();

    const { data: reservations = [], isLoading } = useQuery({
        queryKey: ['reservations', projectId],
        queryFn: () => reservationsApi.getReservations(projectId!),
        enabled: !!projectId
    });

    const updateMutation = useMutation({
        mutationFn: (data: { id: string; attended: boolean }) =>
            reservationsApi.updateAttendance(data.id, data.attended),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reservations', projectId] });
            toast.success('更新しました');
        },
        onError: () => {
            toast.error('更新に失敗しました');
        }
    });

    const handleDownloadCsv = async () => {
        try {
            const blob = await reservationsApi.exportCsv(projectId!);
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `reservations_${format(new Date(), 'yyyyMMdd_HHmm')}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (e) {
            toast.error('ダウンロードに失敗しました');
        }
    };

    if (isLoading) return <Loading />;

    // Group by milestone for better view
    const grouped = reservations.reduce((acc: Record<string, ReservationResponse[]>, curr: ReservationResponse) => {
        const key = curr.milestone_title || '不明な公演';
        if (!acc[key]) acc[key] = [];
        acc[key].push(curr);
        return acc;
    }, {} as Record<string, ReservationResponse[]>);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-gray-900">予約管理</h1>
                <button
                    onClick={handleDownloadCsv}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                    CSVダウンロード
                </button>
            </div>

            {Object.entries(grouped).map(([title, items]) => (
                <div key={title} className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
                    <div className="px-4 py-5 sm:px-6 bg-gray-50 border-b border-gray-200">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">
                            {title}
                        </h3>
                        <p className="mt-1 max-w-2xl text-sm text-gray-500">
                            合計: {items.reduce((sum: number, r: ReservationResponse) => sum + r.count, 0)}名 / {items.length}件
                        </p>
                    </div>
                    <ul role="list" className="divide-y divide-gray-200">
                        {items.map((reservation: ReservationResponse) => (
                            <li key={reservation.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                                <div className="flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center space-x-3">
                                            <p className={`text-sm font-medium truncate ${reservation.attended ? 'text-gray-500 line-through' : 'text-indigo-600'}`}>
                                                {reservation.name}
                                            </p>
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                {reservation.count}枚
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
                                                紹介者: {reservation.referral_name}
                                            </div>
                                        )}
                                    </div>
                                    <div className="ml-4 flex-shrink-0 flex flex-col items-end space-y-2">
                                        <p className="text-xs text-gray-400">
                                            予約: {format(new Date(reservation.created_at), 'MM/dd HH:mm')}
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
                                            {reservation.attended ? '出席済' : '未出席'}
                                        </span>
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            ))}

            {reservations.length === 0 && (
                <div className="text-center py-10 text-gray-500">
                    予約はまだありません
                </div>
            )}
        </div>
    );
};
