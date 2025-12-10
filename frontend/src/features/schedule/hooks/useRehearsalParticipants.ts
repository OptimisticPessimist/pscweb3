import { useState, useEffect } from 'react';
import type { Rehearsal, RehearsalParticipantState } from '@/types';

export const useRehearsalParticipants = (
    isOpen: boolean,
    members: any[] | undefined,
    script: any | undefined,
    sceneIds: string[],
    rehearsal?: Rehearsal | null
) => {
    const [participantsState, setParticipantsState] = useState<Record<string, RehearsalParticipantState>>({});
    const [isRehearsalDataLoaded, setIsRehearsalDataLoaded] = useState(false);

    // 1. Auto-Calculation (Based on Scene Selection)
    useEffect(() => {
        if (!members || !script) return;

        setParticipantsState((prevState) => {
            const newState: Record<string, RehearsalParticipantState> = { ...prevState };

            // Identify needed casts from currently selected scenes
            const targetScenes = script.scenes.filter((s: any) => sceneIds.includes(s.id));
            const neededCasts: Record<string, string> = {}; // userId -> characterId

            targetScenes.forEach((scene: any) => {
                scene.lines.forEach((line: any) => {
                    line.character.castings.forEach((casting: any) => {
                        neededCasts[casting.user_id] = line.character.id;
                    });
                });
            });

            // Iterate members and update status
            members.forEach(m => {
                const uid = m.user_id;
                const isCast = !!neededCasts[uid];
                const castCharacterId = neededCasts[uid] || null;

                if (!newState[uid]) {
                    // New entry
                    newState[uid] = {
                        checked: isCast || !!m.default_staff_role,
                        staffRole: m.default_staff_role || null,
                        isCast: isCast,
                        castCharacterId: castCharacterId,
                        userName: m.discord_username,
                        displayName: m.display_name
                    };
                } else {
                    // Update existing entry
                    const wasCast = newState[uid].isCast;
                    newState[uid].isCast = isCast;
                    newState[uid].castCharacterId = castCharacterId;

                    // If newly became cast, auto-check
                    if (isCast && !wasCast) {
                        newState[uid].checked = true;
                    }
                    newState[uid].userName = m.discord_username;
                    newState[uid].displayName = m.display_name;
                }
            });
            return newState;
        });
    }, [sceneIds, members, script]);

    // 2. Data Patching (One-time from Rehearsal Data)
    useEffect(() => {
        if (isOpen && rehearsal && members && !isRehearsalDataLoaded) {
            setParticipantsState(prev => {
                const newState = { ...prev };
                members.forEach((m: any) => {
                    const p = rehearsal.participants?.find((rp: any) => rp.user_id === m.user_id);
                    const c = rehearsal.casts?.find((rc: any) => rc.user_id === m.user_id);

                    const isParticipant = !!p;
                    const isCastFromDB = !!c;

                    if (newState[m.user_id]) {
                        newState[m.user_id].checked = isParticipant || isCastFromDB;
                        if (p?.staff_role) {
                            newState[m.user_id].staffRole = p.staff_role;
                        }
                    }
                });
                return newState;
            });
            setIsRehearsalDataLoaded(true);
        } else if (!isOpen) {
            setIsRehearsalDataLoaded(false);
            setParticipantsState({}); // Reset on close
        }
    }, [isOpen, rehearsal, members, isRehearsalDataLoaded]);

    return { participantsState, setParticipantsState };
};
