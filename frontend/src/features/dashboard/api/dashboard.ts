import { apiClient } from '@/api/client';

export interface Project {
    id: string;
    name: string;
    description: string | null;
    discord_webhook_url: string | null;
    created_at: string;
    role: 'owner' | 'editor' | 'viewer'; // ProjectMemberからの結合データ
}

export interface ActivityItem {
    type: string;
    title: string;
    description: string | null;
    timestamp: string;
    user_name: string | null;
}

export interface RehearsalInfo {
    id: string;
    title: string;
    start_time: string;
    end_time: string;
    location: string | null;
}

export interface MilestoneInfo {
    id: string;
    title: string;
    start_date: string;
    end_date: string | null;
    location: string | null;
    days_until: number;
}

export interface DashboardResponse {
    next_rehearsal: RehearsalInfo | null;
    next_milestone: MilestoneInfo | null;
    pending_attendance_count: number;
    total_members: number;
    recent_activities: ActivityItem[];
}

export const dashboardApi = {
    getProjects: async (): Promise<Project[]> => {
        const response = await apiClient.get<Project[]>('/projects/');
        return response.data;
    },

    createProject: async (data: { name: string; description?: string }): Promise<Project> => {
        const response = await apiClient.post<Project>('/projects/', data);
        return response.data;
    },

    deleteProject: async (id: string): Promise<void> => {
        await apiClient.delete(`/projects/${id}`);
    },

    getDashboard: async (projectId: string): Promise<DashboardResponse> => {
        const response = await apiClient.get<DashboardResponse>(`/projects/${projectId}/dashboard`);
        return response.data;
    },
};
