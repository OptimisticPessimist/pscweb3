import { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import toast from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import type { AttendanceEventResponse } from '@/features/attendance/api/attendance';
import { downloadAttendanceExport } from '@/features/attendance/utils/attendanceExport';

interface AttendanceExportControlProps {
    projectId: string;
    events: AttendanceEventResponse[];
    compact?: boolean;
}

export const AttendanceExportControl: React.FC<AttendanceExportControlProps> = ({
    projectId,
    events,
    compact = false,
}) => {
    const { t } = useTranslation();
    const [selectedEventId, setSelectedEventId] = useState(events[0]?.id ?? '');

    useEffect(() => {
        if (!events.some((event) => event.id === selectedEventId)) {
            setSelectedEventId(events[0]?.id ?? '');
        }
    }, [events, selectedEventId]);

    const selectedEvent = events.find((event) => event.id === selectedEventId);

    const exportMutation = useMutation({
        mutationFn: async () => {
            if (!selectedEvent) return;
            await downloadAttendanceExport(projectId, selectedEvent);
        },
        onSuccess: () => {
            toast.success(t('attendance.exportSuccess'));
        },
        onError: () => {
            toast.error(t('attendance.exportFailed'));
        },
    });

    if (events.length === 0) return null;

    const buttonClassName = compact
        ? 'inline-flex items-center justify-center px-2.5 py-1.5 text-xs font-medium rounded-md border border-indigo-200 text-indigo-700 bg-white hover:bg-indigo-50 disabled:opacity-50'
        : 'inline-flex items-center justify-center px-3 py-2 text-sm font-medium rounded-md border border-indigo-200 text-indigo-700 bg-white hover:bg-indigo-50 disabled:opacity-50';

    return (
        <div className={compact ? 'flex items-center gap-2' : 'flex items-center gap-3'}>
            {events.length > 1 && (
                <select
                    value={selectedEventId}
                    onChange={(event) => setSelectedEventId(event.target.value)}
                    className="max-w-48 rounded-md border-gray-300 text-xs focus:border-indigo-500 focus:ring-indigo-500"
                    aria-label={t('attendance.exportEventSelect')}
                >
                    {events.map((event) => (
                        <option key={event.id} value={event.id}>
                            {event.title}
                        </option>
                    ))}
                </select>
            )}
            <button
                type="button"
                onClick={() => exportMutation.mutate()}
                disabled={!selectedEvent || exportMutation.isPending}
                className={buttonClassName}
                title={t('attendance.exportJson')}
            >
                <Download className={compact ? 'h-3.5 w-3.5 mr-1' : 'h-4 w-4 mr-1.5'} />
                {t('attendance.exportJson')}
            </button>
        </div>
    );
};
