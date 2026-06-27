import { attendanceApi, type AttendanceEventResponse } from '@/features/attendance/api/attendance';
import type { Project } from '@/types';

export const canExportAttendance = (role?: Project['role'] | null) =>
    role === 'owner' || role === 'editor';

export const findAttendanceEventsForRehearsal = (
    events: AttendanceEventResponse[],
    rehearsalId: string | null | undefined,
    scheduleDate: string | null | undefined,
) => {
    return events.filter((event) => {
        if (event.rehearsal_id !== null && event.rehearsal_id !== undefined) {
            return rehearsalId != null && event.rehearsal_id === rehearsalId;
        }
        // rehearsal_id 未設定の既存データはタイムスタンプで照合
        if (!scheduleDate || !event.schedule_date) return false;
        const targetTime = parseApiDateAsUtcTime(scheduleDate);
        const eventTime = parseApiDateAsUtcTime(event.schedule_date);
        return !Number.isNaN(targetTime) && !Number.isNaN(eventTime) && Math.abs(eventTime - targetTime) < 1000;
    });
};

const parseApiDateAsUtcTime = (value: string) => {
    const trimmedValue = value.trim();
    const dateOnlyPattern = /^\d{4}-\d{2}-\d{2}$/;
    const timezonePattern = /(?:[zZ]|[+-]\d{2}:?\d{2})$/;
    let normalizedValue = trimmedValue;

    if (dateOnlyPattern.test(trimmedValue)) {
        normalizedValue = `${trimmedValue}T00:00:00Z`;
    } else if (!timezonePattern.test(trimmedValue)) {
        normalizedValue = `${trimmedValue}Z`;
    }

    return new Date(normalizedValue).getTime();
};

export const buildFallbackFilename = (event: AttendanceEventResponse) => {
    return `attendance-${event.id}.json`;
};

export const downloadAttendanceExport = async (
    projectId: string,
    event: AttendanceEventResponse,
) => {
    const { blob, filename } = await attendanceApi.exportAttendanceEvent(projectId, event.id);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || buildFallbackFilename(event);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};
