import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rehearsalsApi } from '../api/rehearsals';
import { scriptsApi } from '@/features/scripts/api/scripts';
import { projectsApi } from '@/features/projects/api/projects';
import type { Rehearsal, RehearsalCreate, RehearsalUpdate, RehearsalParticipantCreate, RehearsalCastCreate } from '@/types';
import { RehearsalParticipants } from './RehearsalParticipants';

interface RehearsalModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: string;
    scheduleId: string;
    scriptId: string;
    initialDate?: Date | null;
    rehearsal?: Rehearsal | null;
}

export const RehearsalModal: React.FC<RehearsalModalProps> = ({
    isOpen,
    onClose,
    projectId,
    scheduleId,
    scriptId,
    initialDate,
    rehearsal,
}) => {
    const queryClient = useQueryClient();
    const [date, setDate] = useState<string>('');
    const [duration, setDuration] = useState<number>(120);
    const [location, setLocation] = useState<string>('');
    const [notes, setNotes] = useState<string>('');
    const [sceneIds, setSceneIds] = useState<string[]>([]);
    const [createAttendance, setCreateAttendance] = useState<boolean>(false);
    const [attendanceDeadline, setAttendanceDeadline] = useState<string>('');
    const [statusMessage, setStatusMessage] = useState<string>('');

    interface ParticipantState {
        checked: boolean;
        staffRole: string | null;
        isCast: boolean;
        castCharacterId: string | null;
        userName: string | null;
        displayName: string | null;
    }
    const [participantsState, setParticipantsState] = useState<Record<string, ParticipantState>>({});

    const { data: script } = useQuery({
        queryKey: ['script', scriptId],
        queryFn: () => scriptsApi.getScript(projectId, scriptId),
        enabled: !!scriptId && isOpen,
    });

    const { data: members } = useQuery({
        queryKey: ['projectMembers', projectId],
        queryFn: () => projectsApi.getProjectMembers(projectId),
        enabled: !!projectId && isOpen,
    });

    // Auto-calculate participants based on scenes
    // This runs when sceneIds change.
    useEffect(() => {
        if (!members || !script) return;

        // If editing existing rehearsal, we initialize state in the other useEffect.
        // However, if user changes scenes, we might want to update cast status.
        // We need to merge current state with new calculations.

        setParticipantsState((prevState) => {
            const newState: Record<string, ParticipantState> = { ...prevState };

            // 1. Identify needed casts from currently selected scenes
            const targetScenes = script.scenes.filter((s: any) => sceneIds.includes(s.id));
            const neededCasts: Record<string, string> = {}; // userId -> characterId

            targetScenes.forEach((scene: any) => {
                scene.lines.forEach((line: any) => {
                    if (line.character && line.character.castings) {
                        line.character.castings.forEach((casting: any) => {
                            neededCasts[casting.user_id] = line.character.id;
                        });
                    }
                });
            });

            // 2. Iterate members and update status
            members.forEach(m => {
                const uid = m.user_id;
                const isCast = !!neededCasts[uid];
                const castCharacterId = neededCasts[uid] || null;

                if (!newState[uid]) {
                    // New entry (only if not existed)
                    newState[uid] = {
                        checked: isCast || !!m.default_staff_role,
                        staffRole: m.default_staff_role || null,
                        isCast: isCast,
                        castCharacterId: castCharacterId,
                        userName: m.discord_username,
                        displayName: m.display_name || null
                    };
                } else {
                    // Update existing entry
                    const wasCast = newState[uid].isCast;
                    newState[uid].isCast = isCast;
                    newState[uid].castCharacterId = castCharacterId;

                    // If newly became cast, auto-check (unless user unchecked it? Hard to know user intent vs old state)
                    // For now, if became cast and wasn't checked, check it.
                    if (isCast && !wasCast) {
                        newState[uid].checked = true;
                    }
                    // Updating names just in case
                    newState[uid].userName = m.discord_username;
                    newState[uid].displayName = m.display_name || null;
                }
            });
            return newState;
        });
    }, [sceneIds, members, script]); // Removed 'rehearsal' dependency to allow updates

    // Initialization Effect
    useEffect(() => {
        if (isOpen) {
            setStatusMessage('');
            if (rehearsal) {
                // Edit Mode
                const d = new Date(rehearsal.date);
                const formattedDate = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                setDate(formattedDate);
                setDuration(rehearsal.duration_minutes);
                setLocation(rehearsal.location || '');
                setNotes(rehearsal.notes || '');

                // Scene IDs
                // Backend might return `scene_ids` or we infer from single `scene_id` if older.
                // Assuming backend update is deployed but data might be mixed.
                // Currently `Rehearsal` type in frontend doesn't have `scene_ids` populated correctly unless we updated type?
                // We updated `RehearsalCreate` type, but `Rehearsal` response type?
                // `Rehearsal` response type implies `scene_id` field.
                // If backend returns `scenes` relation? We need to use it.
                // Since Type might be missing `scenes` or `scene_ids` in response interface (I didn't update Rehearsal response interface),
                // we might need to rely on `scene_id` for now or assume `any`.
                // Better approach: Use whatever we have.
                const r = rehearsal as any;
                if (r.scenes && Array.isArray(r.scenes)) {
                    setSceneIds(r.scenes.map((s: any) => s.id));
                } else if (rehearsal.scene_id) {
                    setSceneIds([rehearsal.scene_id]);
                } else {
                    setSceneIds([]);
                }

                // Initialize Participants State
                // We need to wait for `members` to be loaded to populate full list.
                // The other useEffect handles `members` dependency.
                // Here we just set basic fields.
                // BUT `participantsState` depends on members to be complete.
                // If members are not loaded yet, the other useEffect will run when they load.
                // We need to ensure that when they load, we respect `rehearsal` data.
                // This is tricky with double useEffects.
                // Solution: Pass `rehearsal` participants to `setParticipantsState` in the other useEffect or here if possible.
                // Let's do nothing here for participantsState, and handle logic in the main useEffect?
                // No, the main useEffect calculates form SCENES.
                // We need to merge: Scenes Logic + Existing Rehearsal Data.
                // Let's force a merged initialization in the main useEffect if `rehearsal` is present?
                // Or use a ref to track "initialized from rehearsal".
            } else if (initialDate) {
                // Create Mode
                const d = new Date(initialDate);
                let formattedDate = '';
                if (isNaN(d.getTime())) {
                    const now = new Date();
                    formattedDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                } else {
                    formattedDate = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                }
                setDate(formattedDate);
                setDuration(120);
                setLocation('');
                setNotes('');
                setSceneIds([]);
                // participantsState will be auto-calc'd empty -> then populated by members default
            }
        }
    }, [isOpen, rehearsal, initialDate]);

    // One-time initialization from Rehearsal Data (when members and rehearsal are both ready)
    const [isRehearsalDataLoaded, setIsRehearsalDataLoaded] = useState(false);
    useEffect(() => {
        if (isOpen && rehearsal && members && !isRehearsalDataLoaded) {
            setParticipantsState(prev => {
                const newState = { ...prev };
                members.forEach(m => {
                    const p = rehearsal.participants?.find((rp: any) => rp.user_id === m.user_id);
                    const c = rehearsal.casts?.find((rc: any) => rc.user_id === m.user_id);

                    // If member exists in rehearsal data, override the "auto-calc" state
                    // If not, keep auto-calc or unchecked?
                    // Generally, if editing, we trust the DB state.
                    const isParticipant = !!p;
                    const isCastFromDB = !!c;

                    if (newState[m.user_id]) {
                        newState[m.user_id].checked = isParticipant || isCastFromDB;
                        newState[m.user_id].staffRole = p?.staff_role || newState[m.user_id].staffRole || null;
                        // For cast info, we trust the scene calc for "isCast" capability, but DB for actual participation?
                        // No, "isCast" is property of Scene. 
                        // "checked" is participation.
                        // So keep "isCast" from Scene Logic.
                    }
                });
                return newState;
            });
            setIsRehearsalDataLoaded(true);
        } else if (!isOpen) {
            setIsRehearsalDataLoaded(false);
        }
    }, [isOpen, rehearsal, members, isRehearsalDataLoaded]);


    const createMutation = useMutation({
        mutationFn: (data: RehearsalCreate) => rehearsalsApi.addRehearsal(scheduleId, data),
        onSuccess: () => {
            setStatusMessage('Success! Closing...');
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
                queryClient.invalidateQueries({ queryKey: ['mySchedule'] });
                onClose();
            }, 1000);
        },
        onError: (error: Error | any) => {
            setStatusMessage(`Error: ${error.message || 'Unknown error'}\n${JSON.stringify(error.response?.data || {}, null, 2)}`);
        }
    });

    const updateMutation = useMutation({
        mutationFn: (data: RehearsalUpdate) => rehearsalsApi.updateRehearsal(rehearsal!.id, data),
        onSuccess: () => {
            setStatusMessage('Success! Closing...');
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
                queryClient.invalidateQueries({ queryKey: ['mySchedule'] });
                onClose();
            }, 1000);
        },
        onError: (error: Error | any) => {
            setStatusMessage(`Error: ${error.message || 'Unknown error'}\n${JSON.stringify(error.response?.data || {}, null, 2)}`);
        }
    });

    const deleteMutation = useMutation({
        mutationFn: () => rehearsalsApi.deleteRehearsal(rehearsal!.id),
        onSuccess: () => {
            setStatusMessage('Deleted. Closing...');
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
                queryClient.invalidateQueries({ queryKey: ['mySchedule'] });
                onClose();
            }, 1000);
        },
        onError: (error: Error | any) => {
            setStatusMessage(`Error deleting: ${error.message || 'Unknown error'}`);
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        try {
            e.preventDefault();
            setStatusMessage('Submitting...');

            if (!date) {
                setStatusMessage('Error: Date is empty!');
                return;
            }

            // Build lists
            const participantsPayload: RehearsalParticipantCreate[] = [];
            const castsPayload: RehearsalCastCreate[] = [];

            Object.entries(participantsState).forEach(([uid, state]) => {
                if (!state.checked) return;

                // Cast Logic: If isCast (based on scene), treat as Cast.
                // NOTE: User might want to be Staff ONLY even if matched as Cast?
                // Current UI doesn't allow separate toggle.
                // Assumption: If 'isCast' is true and checked, they are attending as Cast.
                if (state.isCast && state.castCharacterId) {
                    castsPayload.push({ user_id: uid, character_id: state.castCharacterId });
                }

                // Staff Logic: If staffRole is set OR (not cast AND checked) -> Staff
                // Also, a Cast can be Staff.
                if (state.staffRole) {
                    participantsPayload.push({ user_id: uid, staff_role: state.staffRole });
                } else if (!state.isCast) {
                    // Checked but not cast -> Generic Staff
                    participantsPayload.push({ user_id: uid, staff_role: null });
                }
            });

            const commonData = {
                date: new Date(date).toISOString(),
                duration_minutes: duration,
                location: location || null,
                notes: notes || null,
                scene_ids: sceneIds,
                participants: participantsPayload,
                casts: castsPayload
            };

            let finalDeadline = attendanceDeadline;
            // If create check is ON but deadline is empty, set to Start Day 08:00 (Local)
            if (createAttendance && !finalDeadline && date) {
                const deadlineDate = new Date(date);
                deadlineDate.setHours(8, 0, 0, 0);
                // Convert to "YYYY-MM-DDTHH:mm" format (Local)
                finalDeadline = new Date(deadlineDate.getTime() - deadlineDate.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
            }

            if (rehearsal) {
                updateMutation.mutate(commonData);
            } else {
                createMutation.mutate({
                    ...commonData,
                    create_attendance_check: createAttendance,
                    attendance_deadline: finalDeadline ? new Date(finalDeadline).toISOString() : null,
                });
            }
        } catch (err: any) {
            console.error('Error in handleSubmit:', err);
            setStatusMessage(`Error in handleSubmit: ${err instanceof Error ? err.message : String(err)}`);
        }
    };

    if (!isOpen) return null;

    return createPortal(
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div
                style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)' }}
                onClick={onClose}
            />
            <div style={{ position: 'relative', backgroundColor: 'white', padding: '2rem', borderRadius: '8px', maxWidth: '800px', width: '100%', maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                        {rehearsal ? 'Edit Rehearsal' : 'New Rehearsal'}
                    </h3>
                    <form onSubmit={handleSubmit} className="mt-5 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Left Column: Basic Info */}
                            <div className="space-y-4">
                                <div>
                                    <label htmlFor="date" className="block text-sm font-medium text-gray-700">Date & Time</label>
                                    <input
                                        type="datetime-local"
                                        id="date"
                                        required
                                        value={date}
                                        onChange={(e) => setDate(e.target.value)}
                                        className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="duration" className="block text-sm font-medium text-gray-700">Duration (min)</label>
                                    <input
                                        type="number"
                                        id="duration"
                                        required
                                        min="15"
                                        step="15"
                                        value={duration}
                                        onChange={(e) => setDuration(parseInt(e.target.value))}
                                        className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="location" className="block text-sm font-medium text-gray-700">Location</label>
                                    <input
                                        type="text"
                                        id="location"
                                        value={location}
                                        onChange={(e) => setLocation(e.target.value)}
                                        className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="notes" className="block text-sm font-medium text-gray-700">Notes</label>
                                    <textarea
                                        id="notes"
                                        rows={2}
                                        value={notes}
                                        onChange={(e) => setNotes(e.target.value)}
                                        className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>

                                {/* Scene Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Scenes</label>
                                    <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2 bg-gray-50">
                                        {script?.scenes && script.scenes.map((scene: any) => (
                                            <div key={scene.id} className="flex items-center mb-1">
                                                <input
                                                    type="checkbox"
                                                    id={`scene-${scene.id}`}
                                                    checked={sceneIds.includes(scene.id)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setSceneIds(prev => [...prev, scene.id]);
                                                        } else {
                                                            setSceneIds(prev => prev.filter(id => id !== scene.id));
                                                        }
                                                    }}
                                                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                                />
                                                <label htmlFor={`scene-${scene.id}`} className="ml-2 text-sm text-gray-900 cursor-pointer">
                                                    S{scene.scene_number} {scene.heading}
                                                </label>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Right Column: Participants */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Participants</label>
                                <div className="max-h-[500px] overflow-y-auto border border-gray-300 rounded-md bg-white">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {members?.map((member: any) => {
                                                const state = participantsState[member.user_id] || { checked: false, staffRole: null, isCast: false };
                                                return (
                                                    <tr key={member.user_id} className={state.checked ? 'bg-indigo-50' : ''}>
                                                        <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                                                            <div className="flex items-center">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={state.checked}
                                                                    onChange={(e) => {
                                                                        const checked = e.target.checked;
                                                                        setParticipantsState(prev => ({
                                                                            ...prev,
                                                                            [member.user_id]: { ...state, checked }
                                                                        }));
                                                                    }}
                                                                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded mr-2"
                                                                />
                                                                <div className="flex flex-col">
                                                                    <span>{member.display_name || member.discord_username}</span>
                                                                    {state.isCast && (
                                                                        <span className="text-xs text-blue-600 bg-blue-100 px-1 rounded inline-block w-fit">
                                                                            🎭 Cast
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                                                            <input
                                                                type="text"
                                                                placeholder={state.isCast ? "(Cast)" : "Role..."}
                                                                value={state.staffRole || ''}
                                                                onChange={(e) => {
                                                                    setParticipantsState(prev => ({
                                                                        ...prev,
                                                                        [member.user_id]: { ...state, staffRole: e.target.value }
                                                                    }));
                                                                }}
                                                                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-xs border-gray-300 rounded-md"
                                                            />
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        {/* Attendance Section */}
                        {!rehearsal && (
                            <div className="border-t border-gray-200 pt-4">
                                <div className="flex items-start">
                                    <div className="flex items-center h-5">
                                        <input
                                            id="create_attendance"
                                            name="create_attendance"
                                            type="checkbox"
                                            checked={createAttendance}
                                            onChange={(e) => setCreateAttendance(e.target.checked)}
                                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                    </div>
                                    <div className="ml-3 text-sm">
                                        <label htmlFor="create_attendance" className="font-medium text-gray-700">Send Attendance Check</label>
                                        <p className="text-gray-500 text-xs">Send a mention message to selected participants via Discord.</p>
                                    </div>
                                </div>
                                {createAttendance && (
                                    <div className="mt-2 ml-7">
                                        <label htmlFor="attendance_deadline" className="block text-xs font-medium text-gray-700">Deadline (30分単位)</label>
                                        <input
                                            type="datetime-local"
                                            id="attendance_deadline"
                                            value={attendanceDeadline}
                                            onChange={(e) => setAttendanceDeadline(e.target.value)}
                                            step="1800"
                                            onBlur={(e) => {
                                                if (!e.target.value) return;
                                                const val = e.target.value;
                                                const d = new Date(val);
                                                const minutes = d.getMinutes();
                                                const remainder = minutes % 30;

                                                if (remainder !== 0) {
                                                    // Round to nearest 30
                                                    if (remainder >= 15) {
                                                        d.setMinutes(minutes + (30 - remainder));
                                                    } else {
                                                        d.setMinutes(minutes - remainder);
                                                    }
                                                    d.setSeconds(0);
                                                    d.setMilliseconds(0);

                                                    // Format: YYYY-MM-DDTHH:mm
                                                    // Adjust for timezone offset for local input
                                                    const newStr = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                                                    setAttendanceDeadline(newStr);
                                                }
                                            }}
                                            className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                        />
                                        <p className="text-xs text-gray-500 mt-1">※00分または30分に自動補正されます</p>
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                            <button
                                type="submit"
                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
                            >
                                {rehearsal ? 'Update' : 'Create'}
                            </button>
                            <button
                                type="button"
                                onClick={onClose}
                                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                            >
                                Cancel
                            </button>
                        </div>

                        {statusMessage && (
                            <div className="mt-4 p-2 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded text-xs break-all whitespace-pre-wrap">
                                <strong>Status:</strong><br />
                                {statusMessage}
                            </div>
                        )}

                        {rehearsal && (
                            <div className="mt-2 border-t pt-4">
                                <button
                                    type="button"
                                    onClick={() => {
                                        if (window.confirm('Are you sure you want to delete this rehearsal?')) {
                                            deleteMutation.mutate();
                                        }
                                    }}
                                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:text-sm"
                                >
                                    Delete Rehearsal
                                </button>
                            </div>
                        )}

                        {rehearsal && (
                            <div className="mt-4 border-t pt-4">
                                <h4 className="text-sm font-medium text-gray-700 mb-2">Detailed Management (Old UI)</h4>
                                <RehearsalParticipants
                                    rehearsal={'scenes' in rehearsal ? rehearsal : { ...rehearsal, scenes: [] }}
                                    projectId={projectId}
                                    sceneCharacters={[]} // We manage this via New UI now, so disabling this prop to simplify
                                />
                            </div>
                        )}
                    </form>
                </div>
            </div>
        </div>,
        document.body
    );
};
