import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Calendar, momentLocalizer, type View } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { reservationsApi } from '../api';
import { PageHead } from '@/components/PageHead';
import { useState } from 'react';

const localizer = momentLocalizer(moment);

export const PublicCalendarPage = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [view, setView] = useState<View>('month');
    const [date, setDate] = useState(new Date());

    const { data: milestones, isLoading } = useQuery({
        queryKey: ['publicSchedule'],
        queryFn: reservationsApi.getPublicSchedule
    });

    const events = milestones?.map(m => ({
        id: m.id,
        title: `${m.project_name} - ${m.title}`,
        start: new Date(m.start_date),
        end: m.end_date ? new Date(m.end_date) : new Date(m.start_date),
        resource: m
    })) || [];

    const handleSelectEvent = (event: any) => {
        navigate(`/reservations/${event.id}`);
    };

    if (isLoading) return <div className="flex justify-center p-10">{t('common.loading')}</div>;

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8 font-sans">
            <PageHead title={t('schedule.calendar.title', 'Event Calendar')} />
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                        {t('schedule.calendar.headline', 'Performance Calendar')}
                    </h1>
                    <p className="mt-3 text-xl text-gray-500">
                        {t('schedule.calendar.subheadline', 'Click on an event to reserve tickets')}
                    </p>
                </div>

                <div className="bg-white shadow rounded-lg p-6">
                    <Calendar
                        localizer={localizer}
                        events={events}
                        startAccessor="start"
                        endAccessor="end"
                        onSelectEvent={handleSelectEvent}
                        view={view}
                        onView={setView}
                        date={date}
                        onNavigate={setDate}
                        style={{ height: 600 }}
                        views={['month', 'week', 'day', 'agenda']}
                        messages={{
                            next: '次へ',
                            previous: '前へ',
                            today: '今日',
                            month: '月',
                            week: '週',
                            day: '日',
                            agenda: '予定',
                            date: '日付',
                            time: '時間',
                            event: 'イベント',
                            noEventsInRange: '期間内にイベントはありません',
                            showMore: (total) => `+${total} 件`
                        }}
                        eventPropGetter={(event) => ({
                            style: {
                                backgroundColor: event.resource?.color || '#3B82F6',
                                borderRadius: '5px',
                                opacity: 0.9,
                                border: '0px',
                                display: 'block',
                                cursor: 'pointer'
                            }
                        })}
                    />
                </div>

                <div className="mt-8 text-center">
                    <a
                        href="/schedule"
                        className="text-indigo-600 hover:text-indigo-900 hover:underline"
                    >
                        ← {t('schedule.calendar.backToList', 'Back to List View')}
                    </a>
                </div>
            </div>
        </div>
    );
};
