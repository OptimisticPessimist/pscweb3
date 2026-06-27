import { describe, expect, it } from 'vitest';
import type { AttendanceEventResponse } from '@/features/attendance/api/attendance';
import { findAttendanceEventsForRehearsal } from '@/features/attendance/utils/attendanceExport';

const createEvent = (
    id: string,
    scheduleDate: string | null,
    rehearsalId: string | null = null,
): AttendanceEventResponse => ({
    id,
    project_id: 'project-1',
    rehearsal_id: rehearsalId,
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

describe('findAttendanceEventsForRehearsal', () => {
    describe('FK-based matching (rehearsal_id set)', () => {
        it('matches by rehearsal_id when set', () => {
            const events = [
                createEvent('matched', '2026-06-27T10:00:00Z', 'rehearsal-1'),
                createEvent('other', '2026-06-27T10:00:00Z', 'rehearsal-2'),
            ];

            const result = findAttendanceEventsForRehearsal(events, 'rehearsal-1', '2026-06-27T10:00:00Z');

            expect(result.map((e) => e.id)).toEqual(['matched']);
        });

        it('does not match by timestamp when rehearsal_id is set but differs', () => {
            const events = [
                createEvent('same-time-different-rehearsal', '2026-06-27T10:00:00Z', 'rehearsal-2'),
            ];

            const result = findAttendanceEventsForRehearsal(events, 'rehearsal-1', '2026-06-27T10:00:00Z');

            expect(result).toEqual([]);
        });

        it('returns no match when rehearsalId is null but event has rehearsal_id', () => {
            const events = [createEvent('event', '2026-06-27T10:00:00Z', 'rehearsal-1')];

            const result = findAttendanceEventsForRehearsal(events, null, '2026-06-27T10:00:00Z');

            expect(result).toEqual([]);
        });
    });

    describe('timestamp fallback matching (rehearsal_id not set)', () => {
        it('matches naive rehearsal dates with UTC attendance dates', () => {
            const events = [
                createEvent('matched', '2026-06-27T10:00:00+00:00'),
                createEvent('different', '2026-06-27T11:00:00+00:00'),
            ];

            const result = findAttendanceEventsForRehearsal(events, 'rehearsal-1', '2026-06-27T10:00:00');

            expect(result.map((e) => e.id)).toEqual(['matched']);
        });

        it('matches dates when both values already include timezone offsets', () => {
            const events = [createEvent('matched', '2026-06-27T19:00:00+09:00')];

            const result = findAttendanceEventsForRehearsal(events, 'rehearsal-1', '2026-06-27T10:00:00Z');

            expect(result.map((e) => e.id)).toEqual(['matched']);
        });

        it('returns no matches for invalid schedule dates', () => {
            const events = [createEvent('matched', '2026-06-27T10:00:00Z')];

            const result = findAttendanceEventsForRehearsal(events, 'rehearsal-1', 'invalid-date');

            expect(result).toEqual([]);
        });
    });

    describe('mixed events (some with rehearsal_id, some without)', () => {
        it('applies FK matching to events with rehearsal_id and timestamp matching to legacy events', () => {
            const events = [
                createEvent('fk-matched', '2026-06-27T10:00:00Z', 'rehearsal-1'),
                createEvent('fk-no-match', '2026-06-27T10:00:00Z', 'rehearsal-2'),
                createEvent('ts-matched', '2026-06-27T10:00:00Z'),
                createEvent('ts-no-match', '2026-06-27T11:00:00Z'),
            ];

            const result = findAttendanceEventsForRehearsal(events, 'rehearsal-1', '2026-06-27T10:00:00Z');

            expect(result.map((e) => e.id)).toEqual(['fk-matched', 'ts-matched']);
        });
    });
});
