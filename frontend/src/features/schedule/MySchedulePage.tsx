import React from 'react';
import { useQuery } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { myScheduleApi } from './api/mySchedule';
import { useTranslation } from 'react-i18next';

export const MySchedulePage: React.FC = () => {
    const { t, i18n } = useTranslation();
    const { data: mySchedule, isLoading } = useQuery({
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

        // Event details
        const typeLabel = props.type === 'rehearsal' ? t('schedule.rehearsal') : t('schedule.milestone');
        const details = `
【${event.title}】

${t('schedule.type')}: ${typeLabel}
${t('project.title')}: ${props.projectName}
${t('schedule.start')}: ${new Date(event.start).toLocaleString(i18n.language)}
${t('schedule.end')}: ${new Date(props.actualEndDate).toLocaleString(i18n.language)}
${props.location ? `${t('schedule.location')}: ${props.location}` : ''}
${props.notes ? `${t('schedule.notes')}: ${props.notes}` : ''}
        `.trim();

        alert(details);
    };

    if (isLoading) return <div className="p-6">{t('common.loading')}</div>;

    return (
        <div className="space-y-6 h-full flex flex-col">
            <div className="bg-white shadow rounded-lg p-6">
                <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('nav.mySchedule')}</h1>
                <p className="text-sm text-gray-600">{t('schedule.allProjectsSchedule')}</p>
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
                    locale={i18n.language}
                />
            </div>
        </div>
    );
};
