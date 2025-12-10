import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/features/projects/api/projects';
import { rehearsalsApi } from '@/features/schedule/api/rehearsals';
import type { Rehearsal } from '@/types';

interface RehearsalParticipantsProps {
    rehearsal: Rehearsal;
    projectId: string;
    sceneCharacters?: { id: string; name: string }[];
}

export const RehearsalParticipants: React.FC<RehearsalParticipantsProps> = ({
    rehearsal,
    projectId,
    sceneCharacters = [],
}) => {
    const queryClient = useQueryClient();
    const [selectedUserId, setSelectedUserId] = useState<string>('');
    const [editingParticipant, setEditingParticipant] = useState<string | null>(null);

    const { data: members } = useQuery({
        queryKey: ['projectMembers', projectId],
        queryFn: () => projectsApi.getProjectMembers(projectId),
    });

    // --- Staff Mutations ---
    const addParticipantMutation = useMutation({
        mutationFn: (userId: string) => rehearsalsApi.addParticipant(rehearsal.id, userId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
            setSelectedUserId('');
        },
    });

    const removeParticipantMutation = useMutation({
        mutationFn: (userId: string) => rehearsalsApi.deleteParticipant(rehearsal.id, userId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
        },
    });

    const updateRoleMutation = useMutation({
        mutationFn: ({ userId, role }: { userId: string; role: string }) =>
            rehearsalsApi.updateParticipantRole(rehearsal.id, userId, role),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
            setEditingParticipant(null);
        },
    });

    // --- Cast Mutations ---
    const addCastMutation = useMutation({
        mutationFn: ({ characterId, userId }: { characterId: string; userId: string }) =>
            rehearsalsApi.addCast(rehearsal.id, characterId, userId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
        },
    });

    const removeCastMutation = useMutation({
        mutationFn: (characterId: string) => rehearsalsApi.deleteCast(rehearsal.id, characterId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
        },
    });

    // Filter available members for Staff addition (exclude those already in staff list)
    // Note: Use can be in Cast AND Staff, so we only filter based on Staff list for Staff addition.
    const availableForStaff = members?.filter(
        m => !rehearsal.participants.some(p => p.user_id === m.user_id)
    );

    return (
        <div className="mt-6 border-t pt-4 space-y-6">

            {/* --- Cast Section --- */}
            {sceneCharacters.length > 0 && (
                <div>
                    <h4 className="text-md font-medium text-gray-900 mb-2">Cast (Characters)</h4>
                    <div className="space-y-2">
                        {sceneCharacters.map(char => {
                            const assignedCast = rehearsal.casts?.find(c => c.character_id === char.id);
                            return (
                                <div key={char.id} className="flex items-center justify-between bg-blue-50 p-2 rounded border border-blue-100">
                                    <div className="flex-1">
                                        <span className="text-sm font-medium text-gray-900 block">{char.name}</span>
                                        <span className="text-xs text-gray-500">
                                            {assignedCast ? `Played by: ${assignedCast.display_name || assignedCast.user_name}` : 'Unassigned'}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {assignedCast ? (
                                            <button
                                                onClick={() => {
                                                    if (window.confirm(`Remove cast for ${char.name}?`)) {
                                                        removeCastMutation.mutate(char.id);
                                                    }
                                                }}
                                                className="text-xs text-red-500 hover:text-red-700"
                                            >
                                                Remove
                                            </button>
                                        ) : (
                                            <select
                                                className="text-xs border-gray-300 rounded shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                                                onChange={(e) => {
                                                    if (e.target.value) {
                                                        addCastMutation.mutate({ characterId: char.id, userId: e.target.value });
                                                        e.target.value = ''; // Reset select
                                                    }
                                                }}
                                                defaultValue=""
                                            >
                                                <option value="" disabled>Assign...</option>
                                                {members?.map(m => (
                                                    <option key={m.user_id} value={m.user_id}>
                                                        {m.display_name || m.discord_username}
                                                    </option>
                                                ))}
                                            </select>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* --- Staff / Participants Section --- */}
            <div>
                <h4 className="text-md font-medium text-gray-900 mb-2">Staff & Participants</h4>

                {/* List Staff */}
                <div className="space-y-2 mb-3">
                    {rehearsal.participants.length === 0 && (
                        <p className="text-xs text-gray-500 italic">No staff assigned.</p>
                    )}
                    {rehearsal.participants.map((participant) => (
                        <div key={participant.user_id} className="flex items-center justify-between bg-gray-50 p-2 rounded border border-gray-200">
                            <div className="flex-1">
                                <span className="text-sm font-medium text-gray-700">{participant.display_name || participant.user_name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                {editingParticipant === participant.user_id ? (
                                    <div className="flex items-center gap-1">
                                        <input
                                            type="text"
                                            defaultValue={participant.staff_role || ''}
                                            id={`role-input-${participant.user_id}`}
                                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-24 sm:text-xs border-gray-300 rounded-md"
                                            placeholder="Role"
                                            autoFocus
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') {
                                                    const input = document.getElementById(`role-input-${participant.user_id}`) as HTMLInputElement;
                                                    updateRoleMutation.mutate({ userId: participant.user_id, role: input.value });
                                                }
                                            }}
                                        />
                                        <button
                                            onClick={() => {
                                                const input = document.getElementById(`role-input-${participant.user_id}`) as HTMLInputElement;
                                                updateRoleMutation.mutate({ userId: participant.user_id, role: input.value });
                                            }}
                                            className="text-xs text-green-600 hover:text-green-800"
                                        >
                                            Save
                                        </button>
                                        <button
                                            onClick={() => setEditingParticipant(null)}
                                            className="text-xs text-gray-500 hover:text-gray-700"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                ) : (
                                    <div
                                        onClick={() => setEditingParticipant(participant.user_id)}
                                        className="text-xs text-gray-500 cursor-pointer hover:text-indigo-600 border-b border-dotted border-gray-400 hover:border-indigo-600"
                                        title="Click to edit role"
                                    >
                                        {participant.staff_role || <span className="italic text-gray-400">No Role</span>}
                                    </div>
                                )}

                                <button
                                    onClick={() => {
                                        if (window.confirm('Remove this participant?')) {
                                            removeParticipantMutation.mutate(participant.user_id);
                                        }
                                    }}
                                    className="text-red-400 hover:text-red-600 ml-2"
                                    title="Remove participant"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Add Staff */}
                <div className="flex gap-2">
                    <select
                        value={selectedUserId}
                        onChange={(e) => setSelectedUserId(e.target.value)}
                        className="block w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="">Add Staff / Participant...</option>
                        {availableForStaff?.map(member => (
                            <option key={member.user_id} value={member.user_id}>
                                {member.display_name || member.discord_username}
                            </option>
                        ))}
                    </select>
                    <button
                        type="button"
                        onClick={() => addParticipantMutation.mutate(selectedUserId)}
                        disabled={!selectedUserId || addParticipantMutation.isPending}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        Add
                    </button>
                </div>
            </div>
        </div>
    );
};
