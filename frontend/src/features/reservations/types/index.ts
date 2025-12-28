export interface ReservationResponse {
    id: string;
    name: string;
    email: string;
    count: number;
    attended: boolean;
    milestone_id: string;
    created_at: string;
    milestone_title?: string;
    referral_name?: string;
    user_id?: string;
}

export interface ReservationCreateRequest {
    milestone_id: string;
    name: string;
    email: string;
    count: number;
    referral_user_id?: string | null;
}

export interface ReservationUpdateRequest {
    attended: boolean;
}

export interface PublicMilestone {
    id: string;
    project_id: string;
    title: string;
    start_date: string;
    end_date?: string;
    location?: string;
    color?: string;
    reservation_capacity?: number;
    current_reservation_count?: number;
    project_name?: string;
}

export interface PublicMember {
    id: string;
    name: string;
}
