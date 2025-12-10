import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { rehearsalsApi } from '../api/rehearsals';
import { scriptsApi } from '@/features/scripts/api/scripts';
import { projectsApi } from '@/features/projects/api/projects';
import { RehearsalModal } from '../components/RehearsalModal';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export const SchedulePage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();
    const [selectedRehearsalId, setSelectedRehearsalId] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);

    const { data: project } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    const { data: schedule, isLoading: isScheduleLoading, error: scheduleError } = useQuery({
        queryKey: ['rehearsalSchedule', projectId],
        queryFn: () => rehearsalsApi.getSchedule(projectId!),
        enabled: !!projectId,
        retry: false,
    });

    const activeRehearsal = selectedRehearsalId
        ? schedule?.rehearsals.find(r => r.id === selectedRehearsalId) || null
        : null;

    const { data: scripts } = useQuery({
        queryKey: ['scripts', projectId],
        queryFn: () => scriptsApi.getScripts(projectId!),
        enabled: !!projectId,
    });

    const createScheduleMutation = useMutation({
        mutationFn: (scriptId: string) => rehearsalsApi.createSchedule(projectId!, scriptId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
        },
    });

    const events = schedule?.rehearsals.map(rehearsal => {
        const startDate = new Date(rehearsal.date);
        const endDate = new Date(startDate.getTime() + rehearsal.duration_minutes * 60000);

        // 月表示で日をまたぐ場合、終了時刻を当日の23:59:59に制限
        // これにより、月表示では1マスに収まる
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
            id: rehearsal.id,
            title: rehearsal.scene_heading
                ? `${rehearsal.scene_heading} (${rehearsal.location || 'TBD'})`
                : `Rehearsal (${rehearsal.location || 'TBD'})`,
            start: rehearsal.date,
            end: displayEnd.toISOString(),
            allDay: false, // 時間イベントとして扱う
            backgroundColor: '#3b82f6', // blue-500
            borderColor: '#2563eb', // blue-600
            extendedProps: {
                type: 'rehearsal',
                actualEndDate: endDate.toISOString(), // 実際の終了時刻を保持
                ...rehearsal
            }
        };
    }) || [];

    const handleDateClick = (arg: any) => {
        setSelectedRehearsalId(null);
        setSelectedDate(arg.date);
        setIsModalOpen(true);
    };

    const handleEventClick = (info: any) => {
        setSelectedRehearsalId(info.event.id);
        setSelectedDate(null);
        setIsModalOpen(true);
    };

    if (isScheduleLoading || !project) return <div className="p-6">Loading schedule...</div>;

    // Handle 404 (No Schedule)
    if (scheduleError || !schedule) {
        const hasScripts = scripts && scripts.length > 0;

        return (
            <div className="flex flex-col items-center justify-center h-full p-6 bg-white shadow rounded-lg">
                <h2 className="text-xl font-bold text-gray-900 mb-4">No Rehearsal Schedule</h2>
                <p className="text-gray-500 mb-6">Create a schedule to start planning rehearsals.</p>

                {hasScripts ? (
                    <div className="space-y-4">
                        <p className="text-sm text-gray-700">Select a script to base the schedule on:</p>
                        <div className="flex gap-2 justify-center flex-wrap">
                            {scripts.map(script => (
                                <button
                                    key={script.id}
                                    onClick={() => createScheduleMutation.mutate(script.id)}
                                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                    disabled={createScheduleMutation.isPending}
                                >
                                    {script.title}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="text-center">
                        <p className="text-red-500 mb-4">No scripts found.</p>
                        <p className="text-sm text-gray-500">Please upload a script in the Scripts section first.</p>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="space-y-6 h-full flex flex-col">
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
                    dateClick={handleDateClick}
                    eventClick={handleEventClick}
                    height="100%"
                />
            </div>

            {schedule && (
                <div className="relative z-50">
                    <ErrorBoundary>
                        <RehearsalModal
                            isOpen={isModalOpen}
                            onClose={() => setIsModalOpen(false)}
                            projectId={projectId!}
                            scheduleId={schedule.id}
                            scriptId={schedule.script_id}
                            initialDate={selectedDate}
                            rehearsal={activeRehearsal}
                        />
                    </ErrorBoundary>
                </div>
            )}
        </div>
    );
};
