import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceApi, type AttendanceEventResponse } from '@/features/attendance/api/attendance';
import { Calendar, Clock, Users, AlertCircle, Bell } from 'lucide-react';

export const AttendancePage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();
    const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

    const { data: events, isLoading } = useQuery({
        queryKey: ['attendance', projectId],
        queryFn: () => attendanceApi.getAttendanceEvents(projectId!),
        enabled: !!projectId,
    });

    const { data: eventDetail } = useQuery({
        queryKey: ['attendance', projectId, expandedEvent],
        queryFn: () => attendanceApi.getAttendanceEvent(projectId!, expandedEvent!),
        enabled: !!projectId && !!expandedEvent,
    });

    const remindMutation = useMutation({
        mutationFn: (eventId: string) => attendanceApi.remindPendingUsers(projectId!, eventId),
        onSuccess: () => {
            alert('リマインダーを送信しました');
        },
        onError: () => {
            alert('リマインダー送信に失敗しました');
        },
    });

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    const sortedEvents = events ? [...events].sort((a, b) => {
        const dateA = new Date(a.schedule_date || a.created_at);
        const dateB = new Date(b.schedule_date || b.created_at);
        return dateB.getTime() - dateA.getTime();
    }) : [];

    // 未回答のイベントのみフィルタリング
    const pendingEvents = sortedEvents.filter(e => e.stats.pending > 0);

    return (
        <div className="p-6 space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">出欠確認</h1>
                <p className="text-sm text-gray-600">プロジェクトの出欠確認一覧</p>
            </div>

            {/* 未回答の出欠確認 */}
            {pendingEvents.length > 0 && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
                    <div className="flex items-center">
                        <AlertCircle className="h-5 w-5 text-yellow-400 mr-3" />
                        <p className="font-medium text-yellow-800">
                            未回答の出欠確認が{pendingEvents.length}件あります
                        </p>
                    </div>
                </div>
            )}

            {/* 出欠確認一覧 */}
            <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">出欠確認一覧</h2>
                </div>
                <div className="divide-y divide-gray-200">
                    {sortedEvents.length === 0 ? (
                        <div className="p-6 text-center text-gray-500">
                            出欠確認はまだありません
                        </div>
                    ) : (
                        sortedEvents.map((event) => (
                            <div key={event.id} className="p-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                                            {event.title}
                                        </h3>
                                        <div className="space-y-1 text-sm text-gray-600">
                                            {event.schedule_date && (
                                                <div className="flex items-center">
                                                    <Calendar className="h-4 w-4 mr-2" />
                                                    <span>
                                                        日時: {new Date(event.schedule_date).toLocaleString('ja-JP', {
                                                            year: 'numeric',
                                                            month: 'short',
                                                            day: 'numeric',
                                                            hour: '2-digit',
                                                            minute: '2-digit'
                                                        })}
                                                    </span>
                                                </div>
                                            )}
                                            {event.deadline && (
                                                <div className="flex items-center">
                                                    <Clock className="h-4 w-4 mr-2" />
                                                    <span>
                                                        回答期限: {new Date(event.deadline).toLocaleString('ja-JP', {
                                                            year: 'numeric',
                                                            month: 'short',
                                                            day: 'numeric',
                                                            hour: '2-digit',
                                                            minute: '2-digit'
                                                        })}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                        <div className="mt-3 flex items-center space-x-4">
                                            <div className="flex items-center space-x-2">
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                    OK: {event.stats.ok}
                                                </span>
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                    NG: {event.stats.ng}
                                                </span>
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                    未回答: {event.stats.pending}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    / 計{event.stats.total}名
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="ml-4 flex flex-col space-y-2">
                                        <button
                                            onClick={() => setExpandedEvent(expandedEvent === event.id ? null : event.id)}
                                            className="text-sm text-indigo-600 hover:text-indigo-500"
                                        >
                                            {expandedEvent === event.id ? '閉じる' : '詳細'}
                                        </button>
                                        {event.stats.pending > 0 && (
                                            <button
                                                onClick={() => remindMutation.mutate(event.id)}
                                                disabled={remindMutation.isPending}
                                                className="flex items-center text-sm text-indigo-600 hover:text-indigo-500 disabled:opacity-50"
                                            >
                                                <Bell className="h-4 w-4 mr-1" />
                                                リマインド
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {/* 詳細表示 */}
                                {expandedEvent === event.id && eventDetail && (
                                    <div className="mt-4 pt-4 border-t border-gray-200">
                                        <h4 className="text-sm font-semibold text-gray-700 mb-3">回答状況</h4>
                                        <div className="space-y-2">
                                            {eventDetail.targets.map((target) => (
                                                <div key={target.user_id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                                                    <span className="text-sm text-gray-900">
                                                        {target.display_name || target.discord_username}
                                                    </span>
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${target.status === 'ok' ? 'bg-green-100 text-green-800' :
                                                        target.status === 'ng' ? 'bg-red-100 text-red-800' :
                                                            'bg-yellow-100 text-yellow-800'
                                                        }`}>
                                                        {target.status === 'ok' ? 'OK' : target.status === 'ng' ? 'NG' : '未回答'}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};
