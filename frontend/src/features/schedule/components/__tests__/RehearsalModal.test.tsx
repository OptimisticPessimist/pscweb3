import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RehearsalModal } from '../RehearsalModal';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Alias mocks
vi.mock('@/features/schedule/api/rehearsals', () => ({
    rehearsalsApi: {
        addRehearsal: vi.fn(),
        updateRehearsal: vi.fn(),
        deleteRehearsal: vi.fn(),
    }
}));
vi.mock('@/features/scripts/api/scripts', () => ({
    scriptsApi: {
        getScript: vi.fn(),
    }
}));
vi.mock('@/features/projects/api/projects', () => ({
    projectsApi: {
        getProjectMembers: vi.fn(),
    }
}));

// Import mocks to assert calls
import { rehearsalsApi } from '@/features/schedule/api/rehearsals';
import { scriptsApi } from '@/features/scripts/api/scripts';
import { projectsApi } from '@/features/projects/api/projects';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: { retry: false },
    },
});

const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('RehearsalModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Setup default mock responses
        (scriptsApi.getScript as any).mockResolvedValue({
            id: 'script-1',
            scenes: [
                {
                    id: 'scene-1', scene_number: 1, heading: 'Entrance', lines: [
                        { character: { id: 'char-1', castings: [{ user_id: 'user-1' }] } }
                    ]
                },
                { id: 'scene-2', scene_number: 2, heading: 'Battle', lines: [] }
            ],
            characters: [{ id: 'char-1', name: 'Hero' }]
        });
        (projectsApi.getProjectMembers as any).mockResolvedValue([
            { user_id: 'user-1', display_name: 'Actor A', discord_username: 'actor_a', role: 'member' },
            { user_id: 'user-2', display_name: 'Staff B', discord_username: 'staff_b', role: 'member', default_staff_role: 'Lighting' }
        ]);
    });

    it('renders correctly when open', async () => {
        render(
            <RehearsalModal
                isOpen={true}
                onClose={() => { }}
                projectId="proj-1"
                scheduleId="sch-1"
                scriptId="script-1"
                initialDate={new Date('2025-12-12T10:00:00')}
            />,
            { wrapper: Wrapper }
        );

        expect(screen.getByText('稽古を追加')).toBeInTheDocument();
        // Wait for data load
        await screen.findByText('Actor A');
        expect(await screen.findByText('Entrance')).toBeInTheDocument();
        expect(screen.getByText('Battle')).toBeInTheDocument();
    });

    it('auto-selects participants when scene is checked', async () => {
        render(
            <RehearsalModal
                isOpen={true}
                onClose={() => { }}
                projectId="proj-1"
                scheduleId="sch-1"
                scriptId="script-1"
            />,
            { wrapper: Wrapper }
        );

        await screen.findByText('Entrance');

        // Check Scene 1
        const sceneCheckbox = screen.getByLabelText('1. Entrance');
        fireEvent.click(sceneCheckbox);

        // Actor A (user-1) is cast in Scene 1 (char-1)
        // Should be auto-selected
        // We need to find the checkbox for Actor A. 
        // The table row for user-1.
        // Simplified: check if checkbox is checked.
        // Assuming user-1 checkbox has some label or we look by role/test-id?
        // UI uses: <input type="checkbox" checked={state.checked} ... /> in a table.
        // It renders displayName.

        // Let's verify via state or DOM logic.
        // The checkbox near "Actor A" should be checked.
        const rows = screen.getAllByRole('row');
        const actorRow = rows.find(r => r.textContent?.includes('Actor A'));
        const checkbox = actorRow?.querySelector('input[type="checkbox"]');
        expect(checkbox).toBeChecked();
    });

    it('submits correct payload with auto-deadline', async () => {
        render(
            <RehearsalModal
                isOpen={true}
                onClose={() => { }}
                projectId="proj-1"
                scheduleId="sch-1"
                scriptId="script-1"
                initialDate={new Date('2025-12-12T10:00:00')}
            />,
            { wrapper: Wrapper }
        );

        await waitFor(() => expect(screen.getByText('Entrance')).toBeInTheDocument());

        // Check Scene 1
        fireEvent.click(screen.getByLabelText('1. Entrance'));

        // Enable Attendance Check
        const attendanceCheck = screen.getByLabelText(/出欠確認を作成する/i);
        fireEvent.click(attendanceCheck);

        // Ensure Deadline is empty (it is by default)

        // Submit
        const submitBtn = screen.getByText('作成');
        fireEvent.click(submitBtn);

        await waitFor(() => {
            expect(rehearsalsApi.addRehearsal).toHaveBeenCalled();
        });

        const callArgs = (rehearsalsApi.addRehearsal as any).mock.calls[0];
        const payload = callArgs[1];
        console.log('Submitted Payload:', JSON.stringify(payload, null, 2));

        // Check auto-deadline exists
        expect(payload.attendance_deadline).toBeDefined();
        expect(payload.scene_ids).toContain('scene-1');
    });
});
