import { apiClient } from '@/api/client';

export interface Project {
    id: string;
    name: string;
    description: string | null;
    discord_webhook_url: string | null;
    created_at: string;
    role: 'owner' | 'editor' | 'viewer'; // ProjectMemberからの結合データ
}


export interface Milestone {
    id: string;
    project_id: string;
    title: string;
    start_date: string;
    end_date: string | null;
    description: string | null;
    color: string | null;
}

export interface ScheduleItem {
    id: string;
    type: 'rehearsal' | 'milestone';
    title: string;
    date: string; // ISO string
    end_date: string | null;
    project_id: string;
    project_name: string;
    description: string | null;
    location?: string | null; // Rehearsal only
    scene_heading?: string | null; // Rehearsal only
    color?: string | null; // Milestone only
}

export interface UserScheduleResponse {
    items: ScheduleItem[];
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

    // Milestones
    getMilestones: async (projectId: string): Promise<Milestone[]> => {
        const response = await apiClient.get<Milestone[]>(`/projects/${projectId}/milestones`);
        return response.data;
    },

    createMilestone: async (projectId: string, data: Omit<Milestone, 'id' | 'project_id'>): Promise<Milestone> => {
        const response = await apiClient.post<Milestone>(`/projects/${projectId}/milestones`, data);
        return response.data;
    },

    deleteMilestone: async (projectId: string, milestoneId: string): Promise<void> => {
        await apiClient.delete(`/projects/${projectId}/milestones/${milestoneId}`);
    },

    // User Schedule
    getMySchedule: async (): Promise<UserScheduleResponse> => {
        const response = await apiClient.get<UserScheduleResponse>('/users/me/schedule');
        return response.data;
    },
};

