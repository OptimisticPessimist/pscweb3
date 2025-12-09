import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rehearsalsApi } from '../api/rehearsals';
import { scriptsApi } from '@/features/scripts/api/scripts';
import type { Rehearsal, RehearsalCreate, RehearsalUpdate } from '@/types';
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
    const [sceneId, setSceneId] = useState<string>('');
    const [statusMessage, setStatusMessage] = useState<string>('');

    // Fetch script scenes
    const { data: script } = useQuery({
        queryKey: ['script', scriptId],
        queryFn: () => scriptsApi.getScript(projectId, scriptId),
        enabled: !!scriptId && isOpen,
    });

    useEffect(() => {
        if (isOpen) {
            setStatusMessage(''); // Reset status on open
            if (rehearsal) {
                // Editing existing rehearsal
                const d = new Date(rehearsal.date);
                // Format for datetime-local: YYYY-MM-DDTHH:mm
                const formattedDate = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                setDate(formattedDate);
                setDuration(rehearsal.duration_minutes);
                setLocation(rehearsal.location || '');
                setNotes(rehearsal.notes || '');
                setSceneId(rehearsal.scene_id || '');
            } else if (initialDate) {
                // Creating new from date click
                const d = new Date(initialDate);
                let formattedDate = '';
                if (isNaN(d.getTime())) {
                    console.error('Invalid date passed to modal:', initialDate);
                    // Fallback to now
                    const now = new Date();
                    formattedDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                } else {
                    formattedDate = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                }
                setDate(formattedDate);
                setDuration(120);
                setLocation('');
                setNotes('');
                setSceneId('');
            }
        }
    }, [isOpen, rehearsal, initialDate]);

    const createMutation = useMutation({
        mutationFn: (data: RehearsalCreate) => rehearsalsApi.addRehearsal(scheduleId, data),
        onSuccess: () => {
            setStatusMessage('Success! Closing...');
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
                onClose();
            }, 1000);
        },
        onError: (error: Error | any) => {
            console.error('Create Rehearsal Error:', error);
            setStatusMessage(`Error: ${error.message || 'Unknown error'}\n${JSON.stringify(error.response?.data || {}, null, 2)}`);
        }
    });

    const updateMutation = useMutation({
        mutationFn: (data: RehearsalUpdate) => rehearsalsApi.updateRehearsal(rehearsal!.id, data),
        onSuccess: () => {
            setStatusMessage('Success! Closing...');
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
                onClose();
            }, 1000);
        },
        onError: (error: Error | any) => {
            console.error('Update Rehearsal Error:', error);
            setStatusMessage(`Error: ${error.message || 'Unknown error'}\n${JSON.stringify(error.response?.data || {}, null, 2)}`);
        }
    });

    const deleteMutation = useMutation({
        mutationFn: () => rehearsalsApi.deleteRehearsal(rehearsal!.id),
        onSuccess: () => {
            setStatusMessage('Deleted. Closing...');
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['rehearsalSchedule', projectId] });
                onClose();
            }, 1000);
        },
        onError: (error: Error | any) => {
            console.error('Delete Rehearsal Error:', error);
            setStatusMessage(`Error deleting: ${error.message || 'Unknown error'}`);
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        try {
            e.preventDefault();
            // console.log('Submitting with date:', date);
            setStatusMessage('Submitting...');

            if (!date) {
                setStatusMessage('Error: Date is empty!');
                return;
            }

            const payload = {
                date: new Date(date).toISOString(),
                duration_minutes: duration,
                location: location || null,
                notes: notes || null,
                scene_id: sceneId || null,
            };

            // Show payload for debugging
            setStatusMessage(`Payload prepared: ${JSON.stringify(payload)}. Sending...`);

            if (rehearsal) {
                updateMutation.mutate(payload);
            } else {
                createMutation.mutate(payload);
            }
        } catch (err: any) {
            console.error('Error in handleSubmit:', err);
            setStatusMessage(`Error in handleSubmit: ${err instanceof Error ? err.message : String(err)}`);
        }
    };

    if (!isOpen) return null;

    return createPortal(
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {/* Backdrop */}
            <div
                style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)' }}
                onClick={onClose}
            />

            {/* Modal Content */}
            <div style={{ position: 'relative', backgroundColor: 'white', padding: '2rem', borderRadius: '8px', maxWidth: '500px', width: '100%', maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                        {rehearsal ? 'Edit Rehearsal' : 'New Rehearsal'}
                    </h3>
                    <form onSubmit={handleSubmit} className="mt-5 space-y-4">
                        <div>
                            <label htmlFor="scene" className="block text-sm font-medium text-gray-700">Scene</label>
                            <select
                                id="scene"
                                value={sceneId}
                                onChange={(e) => setSceneId(e.target.value)}
                                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                            >
                                <option value="">-- No Scene --</option>
                                {script?.scenes && script.scenes.map(scene => (
                                    <option key={scene.id} value={scene.id}>
                                        S{scene.scene_number} {scene.heading}
                                    </option>
                                ))}
                            </select>
                        </div>

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
                            <label htmlFor="duration" className="block text-sm font-medium text-gray-700">Duration (minutes)</label>
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
                                rows={3}
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                            />
                        </div>

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
                                style={rehearsal ? {} : { gridColumn: '1 / -1' }}
                            >
                                Cancel
                            </button>
                        </div>

                        {/* Debug Message Area */}
                        {statusMessage && (
                            <div className="mt-4 p-2 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded text-xs break-all whitespace-pre-wrap">
                                <strong>Debug Status:</strong><br />
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
                            <RehearsalParticipants
                                rehearsal={rehearsal}
                                projectId={projectId}
                                sceneCharacters={
                                    script?.scenes?.find((s: any) => s.id === sceneId)?.lines.reduce((acc: any[], line: any) => {
                                        if (!acc.find(c => c.id === line.character.id)) {
                                            acc.push(line.character);
                                        }
                                        return acc;
                                    }, []) || []
                                }
                            />
                        )}
                    </form>
                </div>
            </div>
        </div>,
        document.body
    );
};
