export interface User {
    id: string;
    discord_id: string;
    discord_username: string;
    screen_name?: string | null;
    discord_avatar_url?: string | null;
    has_premium_password?: boolean;
    created_at: string;
}

export interface UserUpdate {
    premium_password?: string;
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
