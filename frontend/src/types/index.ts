export interface User {
    id: string;
    email: string;
    name: string;
    discord_id: string;
    avatar_url?: string;
}

export interface Project {
    id: string;
    name: string;
    description?: string;
    owner_id: string;
    created_at: string;
    updated_at: string;
    role?: 'owner' | 'admin' | 'editor' | 'viewer';
}
