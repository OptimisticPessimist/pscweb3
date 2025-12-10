export interface User {
    id: string;
    discord_id: string;
    discord_username: string;
    email?: string;
    display_name?: string;
    avatar_url?: string;
    created_at: string;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
}

export interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}
