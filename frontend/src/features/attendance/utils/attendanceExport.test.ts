import { describe, expect, it } from 'vitest';
import type { AttendanceEventResponse } from '@/features/attendance/api/attendance';
import { findAttendanceEventsForScheduleDate } from '@/features/attendance/utils/attendanceExport';

const createEvent = (
    id: string,
    scheduleDate: string | null,
): AttendanceEventResponse => ({
    id,
    project_id: 'project-1',
    title: `event-${id}`,
    schedule_date: scheduleDate,
    deadline: null,
    completed: false,
    created_at: '2026-06-27T00:00:00Z',
    stats: {
        ok: 0,
        ng: 0,
        pending: 0,
        total: 0,
    },
});

describe('findAttendanceEventsForScheduleDate', () => {
    it('matches naive rehearsal dates with UTC attendance dates', () => {
        const events = [
            createEvent('matched', '2026-06-27T10:00:00+00:00'),
            createEvent('different', '2026-06-27T11:00:00+00:00'),
        ];

        const result = findAttendanceEventsForScheduleDate(events, '2026-06-27T10:00:00');

        expect(result.map((event) => event.id)).toEqual(['matched']);
    });

    it('matches dates when both values already include timezone offsets', () => {
        const events = [
            createEvent('matched', '2026-06-27T19:00:00+09:00'),
        ];

        const result = findAttendanceEventsForScheduleDate(events, '2026-06-27T10:00:00Z');

        expect(result.map((event) => event.id)).toEqual(['matched']);
    });

    it('returns no matches for invalid schedule dates', () => {
        const events = [createEvent('matched', '2026-06-27T10:00:00Z')];

        const result = findAttendanceEventsForScheduleDate(events, 'invalid-date');

        expect(result).toEqual([]);
    });
});
