import React from 'react';
import { useQuery } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { myScheduleApi } from './api/mySchedule';

export const MySchedulePage: React.FC = () => {
    const { data: mySchedule, isLoading, error } = useQuery({
        queryKey: ['mySchedule'],
        queryFn: () => myScheduleApi.getMySchedule(),
    });

    const events = mySchedule?.events.map(event => {
        const startDate = new Date(event.start);
        const endDate = event.end ? new Date(event.end) : new Date(startDate.getTime() + 120 * 60000);

        // 月表示で日をまたぐ場合、終了時刻を当日の23:59:59に制限
        const isSameDay = startDate.getDate() === endDate.getDate() &&
            startDate.getMonth() === endDate.getMonth() &&
            startDate.getFullYear() === endDate.getFullYear();

        const displayEnd = isSameDay ? endDate : new Date(
            startDate.getFullYear(),
            startDate.getMonth(),
            startDate.getDate(),
            23, 59, 59
        );

        return {
            id: event.id,
            title: event.title,
            start: event.start,
            end: displayEnd.toISOString(),
            allDay: false,
            backgroundColor: event.project_color,
            borderColor: event.project_color,
            extendedProps: {
                type: event.type,
                projectId: event.project_id,
                projectName: event.project_name,
                location: event.location,
                notes: event.notes,
                actualEndDate: endDate.toISOString(),
            }
        };
    }) || [];

    const handleEventClick = (info: any) => {
        const event = info.event;
        const props = event.extendedProps;

        // イベント詳細をalertで表示（簡易版）
        const details = `
【${event.title}】

種類: ${props.type === 'rehearsal' ? '稽古' : 'マイルストーン'}
プロジェクト: ${props.projectName}
開始: ${new Date(event.start).toLocaleString('ja-JP')}
終了: ${new Date(props.actualEndDate).toLocaleString('ja-JP')}
${props.location ? `場所: ${props.location}` : ''}
${props.notes ? `備考: ${props.notes}` : ''}
        `.trim();

        alert(details);
    };

    if (isLoading) return <div className="p-6">Loading...</div>;

    return (
        <div className="space-y-6 h-full flex flex-col">
            <div className="bg-white shadow rounded-lg p-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">My Schedule</h1>
                <p className="text-sm text-gray-600">参加している全プロジェクトの予定</p>

                {/* Debug Info */}
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-xs">
                    <p><strong>Debug:</strong></p>
                    <p>Loading: {isLoading ? 'Yes' : 'No'}</p>
                    <p>API Response: {mySchedule ? 'Loaded' : 'None'}</p>
                    <p>Error: {error ? (error as any).message || 'Yes' : 'None'}</p>
                    {error && (
                        <pre className="mt-2 p-2 bg-red-50 border border-red-200 rounded overflow-auto max-h-40">
                            {JSON.stringify((error as any).response?.data || error, null, 2)}
                        </pre>
                    )}
                    <p>Events Count: {mySchedule?.events?.length || 0}</p>
                    <p>Calendar Events: {events.length}</p>
                    {mySchedule?.events && mySchedule.events.length > 0 && (
                        <p>Sample Event: {JSON.stringify(mySchedule.events[0]).slice(0, 100)}...</p>
                    )}
                </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6 flex-1">
                <FullCalendar
                    plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                    initialView="dayGridMonth"
                    headerToolbar={{
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,timeGridWeek,timeGridDay'
                    }}
                    events={events}
                    eventClick={handleEventClick}
                    height="100%"
                    locale="ja"
                />
            </div>
        </div>
    );
};
