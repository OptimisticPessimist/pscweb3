import { apiClient as axios } from '@/api/client';
import type {
    ReservationResponse,
    ReservationCreateRequest,
    ReservationUpdateRequest,
    PublicMilestone,
    PublicMember
} from '../types';

export const reservationsApi = {
    // Public
    getMilestone: async (id: string): Promise<PublicMilestone> => {
        const response = await axios.get<PublicMilestone>(`/public/milestones/${id}`);
        return response.data;
    },

    createReservation: async (data: ReservationCreateRequest): Promise<ReservationResponse> => {
        const response = await axios.post<ReservationResponse>('/public/reservations', data);
        return response.data;
    },

    getProjectMembers: async (projectId: string, role?: string): Promise<PublicMember[]> => {
        const response = await axios.get<PublicMember[]>(`/public/projects/${projectId}/members`, {
            params: { role }
        });
        return response.data;
    },

    cancelReservation: async (data: { reservation_id: string; email: string }): Promise<void> => {
        await axios.post('/public/reservations/cancel', data);
    },

    getPublicSchedule: async (): Promise<PublicMilestone[]> => {
        const response = await axios.get<PublicMilestone[]>('/public/schedule');
        return response.data;
    },

    // Internal
    getReservations: async (projectId: string): Promise<ReservationResponse[]> => {
        const response = await axios.get<ReservationResponse[]>(`/projects/${projectId}/reservations`);
        return response.data;
    },

    updateAttendance: async (reservationId: string, attended: boolean): Promise<ReservationResponse> => {
        const response = await axios.patch<ReservationResponse>(`/reservations/${reservationId}/attendance`, {
            attended
        } as ReservationUpdateRequest);
        return response.data;
    },

    exportCsv: async (projectId: string) => {
        const response = await axios.post(`/projects/${projectId}/reservations/export`, {}, {
            responseType: 'blob',
        });
        return response.data;
    },

    // 🆕 マイルストーン別予約一覧取得
    getMilestoneReservations: async (milestoneId: string): Promise<ReservationResponse[]> => {
        const response = await axios.get<ReservationResponse[]>(`/milestones/${milestoneId}/reservations`);
        return response.data;
    },
};
