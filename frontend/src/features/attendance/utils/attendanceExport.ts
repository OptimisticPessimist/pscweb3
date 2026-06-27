import { attendanceApi, type AttendanceEventResponse } from '@/features/attendance/api/attendance';
import type { Project } from '@/types';

export const canExportAttendance = (role?: Project['role'] | null) =>
    role === 'owner' || role === 'editor';

export const findAttendanceEventsForScheduleDate = (
    events: AttendanceEventResponse[],
    scheduleDate: string | null | undefined,
) => {
    if (!scheduleDate) return [];

    const targetTime = parseApiDateAsUtcTime(scheduleDate);
    if (Number.isNaN(targetTime)) return [];

    return events.filter((event) => {
        if (!event.schedule_date) return false;
        const eventTime = parseApiDateAsUtcTime(event.schedule_date);
        return !Number.isNaN(eventTime) && Math.abs(eventTime - targetTime) < 1000;
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

const buildFallbackFilename = (event: AttendanceEventResponse) => {
    const baseDate = event.schedule_date || event.created_at;
    const date = new Date(baseDate);
    const datePart = Number.isNaN(date.getTime())
        ? event.id
        : `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}-${String(date.getHours()).padStart(2, '0')}${String(date.getMinutes()).padStart(2, '0')}`;

    return `attendance-${datePart}.json`;
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
