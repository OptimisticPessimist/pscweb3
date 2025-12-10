import { apiClient } from '@/api/client';

export interface AttendanceStats {
    ok: number;
    ng: number;
    pending: number;
    total: number;
}

export interface AttendanceEventResponse {
    id: string;
    project_id: string;
    title: string;
    schedule_date: string | null;
    deadline: string | null;
    completed: boolean;
    created_at: string;
    stats: AttendanceStats;
}

export interface AttendanceTargetResponse {
    user_id: string;
    display_name: string | null;
    discord_username: string;
    status: 'pending' | 'ok' | 'ng';
}

export interface AttendanceEventDetailResponse extends AttendanceEventResponse {
    targets: AttendanceTargetResponse[];
}

export const attendanceApi = {
    // 出欠確認一覧を取得
    getAttendanceEvents: async (projectId: string): Promise<AttendanceEventResponse[]> => {
        const response = await apiClient.get<AttendanceEventResponse[]>(`/projects/${projectId}/attendance`);
        return response.data;
    },

    // 出欠確認詳細を取得
    getAttendanceEvent: async (projectId: string, eventId: string): Promise<AttendanceEventDetailResponse> => {
        const response = await apiClient.get<AttendanceEventDetailResponse>(`/projects/${projectId}/attendance/${eventId}`);
        return response.data;
    },

    // Pendingユーザーにリマインダー送信
    remindPendingUsers: async (projectId: string, eventId: string): Promise<{ message: string }> => {
        const response = await apiClient.post<{ message: string }>(`/projects/${projectId}/attendance/${eventId}/remind-pending`);
        return response.data;
    },

    // 自分の出欠確認ステータスを更新
    updateMyAttendanceStatus: async (
        projectId: string,
        eventId: string,
        status: 'ok' | 'ng' | 'pending'
    ): Promise<AttendanceEventDetailResponse> => {
        const response = await apiClient.patch<AttendanceEventDetailResponse>(
            `/projects/${projectId}/attendance/${eventId}/my-status`,
            { status }
        );
        return response.data;
    },
};
