export interface User {
    id: string;
    email?: string;
    // name: string; // Deprecated or mapped to display_name
    display_name?: string;
    discord_id: string;
    avatar_url?: string;
    discord_username: string;
}

export interface Project {
    id: string;
    name: string;
    description: string | null;
    created_at: string;
    updated_at?: string; // Optional if not always present
    discord_webhook_url: string | null;
    discord_channel_id: string | null;
    role: 'owner' | 'editor' | 'viewer';
}

export interface ScriptSummary {
    id: string;
    project_id: string;
    title: string;
    uploaded_at: string;
    revision: number;
}

export interface Script extends ScriptSummary {
    characters: { id: string; name: string }[];
    scenes: {
        id: string;
        act_number: number | null;
        scene_number: number;
        heading: string;
        description: string | null;
        lines: { id: string; character: { id: string; name: string }; content: string; order: number }[];
    }[];
}
export interface CharacterInScene {
    id: string;
    name: string;
}

export interface SceneInChart {
    act_number?: number | null;
    scene_number: number;
    scene_heading: string;
    characters: CharacterInScene[];
}

export interface SceneChart {
    id: string;
    script_id: string;
    created_at: string;
    updated_at: string;
    scenes: SceneInChart[];
}

export interface CastingUser {
    user_id: string;
    discord_username: string;
    display_name?: string | null;
    cast_name: string | null;
}

export interface CharacterWithCastings {
    id: string;
    name: string;
    castings: CastingUser[];
}

export interface ProjectMember {
    user_id: string;
    discord_username: string;
    role: 'owner' | 'editor' | 'viewer';
    default_staff_role?: string | null;
    display_name?: string | null;
    joined_at: string;
}

// Rehearsal Types
export interface RehearsalParticipant {
    user_id: string;
    user_name: string;
    display_name?: string | null;
    staff_role: string | null;
}

export interface RehearsalCast {
    character_id: string;
    character_name: string;
    user_id: string;
    user_name: string;
    display_name?: string | null;
}

export interface Rehearsal {
    id: string;
    schedule_id: string;
    scene_id: string | null;
    scene_heading: string | null;
    date: string;
    duration_minutes: number;
    location: string | null;
    notes: string | null;
    participants: RehearsalParticipant[];
    casts: RehearsalCast[];
    scenes?: { id: string; heading: string; scene_number: number }[];
}

export type RehearsalResponse = Rehearsal;

export interface RehearsalScheduleResponse {
    id: string;
    project_id: string;
    script_id: string;
    script_title: string;
    created_at: string;
    rehearsals: Rehearsal[];
}

export interface RehearsalParticipantCreate {
    user_id: string;
    staff_role?: string | null;
}

export interface RehearsalCastCreate {
    user_id: string;
    character_id: string;
}

export interface RehearsalParticipantState {
    checked: boolean;
    staffRole: string | null;
    isCast: boolean;
    castCharacterId: string | null;
    userName: string | null;
    displayName: string | null;
}

export interface RehearsalCreate {
    scene_id?: string | null; // Deprecated
    scene_ids?: string[];
    date: string;
    duration_minutes: number;
    location?: string | null;
    notes?: string | null;
    create_attendance_check?: boolean;
    attendance_deadline?: string | null;
    participants?: RehearsalParticipantCreate[];
    casts?: RehearsalCastCreate[];
}

export interface RehearsalUpdate {
    scene_id?: string | null;
    scene_ids?: string[];
    date?: string | null;
    duration_minutes?: number | null;
    location?: string | null;
    notes?: string | null;
    participants?: RehearsalParticipantCreate[];
    casts?: RehearsalCastCreate[];
}

// Invitation Types
export interface InvitationCreate {
    max_uses?: number | null;
    expires_in_hours?: number;
}

export interface InvitationResponse {
    token: string;
    project_id: string; // Backend sends int/UUID but TS sees string
    project_name: string;
    created_by: string;
    expires_at: string;
    max_uses: number | null;
    used_count: number;
}

export interface InvitationAcceptResponse {
    project_id: string;
    project_name: string;
    message: string;
}

export interface ApiError extends Error {
    response?: {
        data?: {
            detail?: string | { loc: (string | number)[]; msg: string }[] | any;
        };
    };
}
