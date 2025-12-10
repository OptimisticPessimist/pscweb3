import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceApi, type AttendanceEventResponse } from '@/features/attendance/api/attendance';
import { Calendar, Clock, Users, AlertCircle, Bell } from 'lucide-react';

export const AttendancePage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();
    const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
    const [filter, setFilter] = useState<'all' | 'pending' | 'ok' | 'ng'>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedEvents, setSelectedEvents] = useState<Set<string>>(new Set());
    const [detailFilter, setDetailFilter] = useState<'all' | 'pending' | 'ok' | 'ng'>('all');

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

    const bulkRemindMutation = useMutation({
        mutationFn: async (eventIds: string[]) => {
            for (const eventId of eventIds) {
                await attendanceApi.remindPendingUsers(projectId!, eventId);
            }
        },
        onSuccess: () => {
            alert(`${selectedEvents.size}件の出欠確認にリマインダーを送信しました`);
            setSelectedEvents(new Set());
        },
        onError: () => {
            alert('一括リマインダー送信に失敗しました');
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

    // フィルタリング
    let filteredEvents = sortedEvents.filter(e => {
        if (filter === 'pending') return e.stats.pending > 0;
        if (filter === 'ok') return e.stats.ok > 0;
        if (filter === 'ng') return e.stats.ng > 0;
        return true; // 'all'
    });

    // 検索フィルタ（イベントタイトルで検索）
    if (searchQuery) {
        filteredEvents = filteredEvents.filter(e =>
            e.title.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }

    // 未回答のイベントのみ（アラート用）
    const pendingEvents = sortedEvents.filter(e => e.stats.pending > 0);

    return (
        <div className="p-6 space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">出欠確認</h1>
                <p className="text-sm text-gray-600">プロジェクトの出欠確認一覧</p>

                {/* 検索バー */}
                <div className="mt-4">
                    <input
                        type="text"
                        placeholder="イベントタイトルで検索..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    />
                </div>

                {/* 一括操作 */}
                {selectedEvents.size > 0 && (
                    <div className="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded flex items-center justify-between">
                        <p className="text-sm text-indigo-800">
                            {selectedEvents.size}件選択中
                        </p>
                        <button
                            onClick={() => bulkRemindMutation.mutate(Array.from(selectedEvents))}
                            disabled={bulkRemindMutation.isPending}
                            className="flex items-center px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50"
                        >
                            <Bell className="h-4 w-4 mr-1" />
                            一括リマインド送信
                        </button>
                    </div>
                )}
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
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-gray-900">出欠確認一覧</h2>
                        <div className="flex space-x-2">
                            <button
                                onClick={() => setFilter('all')}
                                className={`px-3 py-1 text-sm rounded ${filter === 'all'
                                    ? 'bg-indigo-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                全て
                            </button>
                            <button
                                onClick={() => setFilter('pending')}
                                className={`px-3 py-1 text-sm rounded ${filter === 'pending'
                                    ? 'bg-yellow-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                未回答
                            </button>
                            <button
                                onClick={() => setFilter('ok')}
                                className={`px-3 py-1 text-sm rounded ${filter === 'ok'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                OK
                            </button>
                            <button
                                onClick={() => setFilter('ng')}
                                className={`px-3 py-1 text-sm rounded ${filter === 'ng'
                                    ? 'bg-red-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                NG
                            </button>
                        </div>
                    </div>
                </div>
                <div className="divide-y divide-gray-200">
                    {filteredEvents.length === 0 ? (
                        <div className="p-6 text-center text-gray-500">
                            {filter === 'all' ? '出欠確認はまだありません' : `${filter === 'pending' ? '未回答' : filter === 'ok' ? 'OK' : 'NG'}の出欠確認はありません`}
                        </div>
                    ) : (
                        filteredEvents.map((event) => {
                            // 回答状況に応じた色分け
                            let borderColor = 'border-l-gray-300'; // デフォルト
                            if (event.stats.pending === 0) {
                                // 全員回答済み
                                borderColor = 'border-l-green-500';
                            } else if (event.stats.pending > event.stats.ok) {
                                // 未回答が多い
                                borderColor = 'border-l-yellow-500';
                            } else if (event.stats.ng > event.stats.ok) {
                                // NGが多い
                                borderColor = 'border-l-red-500';
                            } else {
                                // 未回答がある
                                borderColor = 'border-l-yellow-400';
                            }

                            return (
                                <div key={event.id} className={`p-6 border-l-4 ${borderColor}`}>
                                    <div className="flex items-start justify-between">
                                        {/* チェックボックス */}
                                        {event.stats.pending > 0 && (
                                            <div className="mr-3 mt-1">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedEvents.has(event.id)}
                                                    onChange={(e) => {
                                                        const newSelected = new Set(selectedEvents);
                                                        if (e.target.checked) {
                                                            newSelected.add(event.id);
                                                        } else {
                                                            newSelected.delete(event.id);
                                                        }
                                                        setSelectedEvents(newSelected);
                                                    }}
                                                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                                />
                                            </div>
                                        )}

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
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="text-sm font-semibold text-gray-700">回答状況</h4>
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={() => setDetailFilter('all')}
                                                        className={`px-2 py-1 text-xs rounded ${detailFilter === 'all' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'
                                                            }`}
                                                    >
                                                        全て
                                                    </button>
                                                    <button
                                                        onClick={() => setDetailFilter('pending')}
                                                        className={`px-2 py-1 text-xs rounded ${detailFilter === 'pending' ? 'bg-yellow-600 text-white' : 'bg-gray-100 text-gray-700'
                                                            }`}
                                                    >
                                                        未回答
                                                    </button>
                                                    <button
                                                        onClick={() => setDetailFilter('ok')}
                                                        className={`px-2 py-1 text-xs rounded ${detailFilter === 'ok' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'
                                                            }`}
                                                    >
                                                        OK
                                                    </button>
                                                    <button
                                                        onClick={() => setDetailFilter('ng')}
                                                        className={`px-2 py-1 text-xs rounded ${detailFilter === 'ng' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700'
                                                            }`}
                                                    >
                                                        NG
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="space-y-2">
                                                {eventDetail.targets
                                                    .filter(target => {
                                                        if (detailFilter === 'all') return true;
                                                        return target.status === detailFilter;
                                                    })
                                                    .map((target) => (
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
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
};
