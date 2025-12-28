import { useLocation, Link, Navigate } from 'react-router-dom';
import type { ReservationResponse, PublicMilestone } from '../types';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export const ReservationCompletedPage = () => {
    const location = useLocation();
    const state = location.state as { reservation: ReservationResponse; milestone: PublicMilestone } | null;

    if (!state) {
        return <Navigate to="/" replace />;
    }

    const { reservation, milestone } = state;

    // Google Calendar URL generation
    const startDate = new Date(milestone.start_date);
    const endDate = milestone.end_date ? new Date(milestone.end_date) : new Date(startDate.getTime() + 2 * 60 * 60 * 1000); // default 2 hours

    const toIso = (d: Date) => d.toISOString().replace(/-|:|\.\d+/g, '');

    const googleCalendarUrl = new URL('https://www.google.com/calendar/render');
    googleCalendarUrl.searchParams.append('action', 'TEMPLATE');
    const eventTitle = milestone.project_name
        ? `【観劇】${milestone.project_name} - ${milestone.title}`
        : `【観劇】${milestone.title}`;
    googleCalendarUrl.searchParams.append('text', eventTitle);
    googleCalendarUrl.searchParams.append('dates', `${toIso(startDate)}/${toIso(endDate)}`);
    if (milestone.location) {
        googleCalendarUrl.searchParams.append('location', milestone.location);
    }
    googleCalendarUrl.searchParams.append('details', `予約者: ${reservation.name}様\n枚数: ${reservation.count}枚\n\n予約ID: ${reservation.id}`);

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
            <div className="max-w-md w-full bg-white rounded-xl shadow-lg overflow-hidden p-8 text-center space-y-6">

                <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
                    <svg className="h-10 w-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                </div>

                <h2 className="text-3xl font-extrabold text-gray-900">
                    予約完了
                </h2>

                <p className="text-gray-500">
                    ご予約ありがとうございます。<br />
                    確認メールを送信しました。
                </p>

                <div className="bg-gray-50 rounded-lg p-4 text-left border border-gray-100">
                    <p className="text-sm text-gray-500 mb-1">予約ID (キャンセル時に必要です)</p>
                    <p className="font-mono font-bold text-lg text-indigo-600 mb-3 select-all">
                        {reservation.id}
                    </p>

                    <p className="text-sm text-gray-500 mb-1">公演</p>
                    <p className="font-bold text-gray-900 mb-3">
                        {milestone.project_name ? `${milestone.project_name} - ` : ''}{milestone.title}
                    </p>

                    <p className="text-sm text-gray-500 mb-1">日時</p>
                    <p className="font-bold text-gray-900 mb-3">
                        {format(new Date(milestone.start_date), 'yyyy年MM月dd日 (EEE) HH:mm', { locale: ja })}
                    </p>

                    <p className="text-sm text-gray-500 mb-1">予約内容</p>
                    <p className="text-gray-900">
                        {reservation.name} 様 / {reservation.count}枚
                    </p>
                </div>

                <div className="space-y-4 pt-4">
                    <a
                        href={googleCalendarUrl.toString()}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                    >
                        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                            {/* Simplified Google Calendar Icon or generic calendar icon */}
                            <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V8h14v12z" />
                        </svg>
                        Googleカレンダーに追加
                    </a>

                    <div className="flex justify-between text-sm px-2">
                        <Link to="/schedule" className="text-gray-500 hover:text-gray-700">
                            スケジュールへ戻る
                        </Link>
                        <Link to="/reservations/cancel" className="text-red-500 hover:text-red-600">
                            予約をキャンセルする
                        </Link>
                    </div>

                    <Link
                        to={`/reservations/${milestone.id}`}
                        className="block text-sm text-indigo-600 hover:text-indigo-500"
                    >
                        別の予約をする
                    </Link>
                </div>
            </div>
        </div>
    );
};
