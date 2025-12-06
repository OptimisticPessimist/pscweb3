import { apiClient } from '@/api/client';

export interface Project {
    id: number;
    name: string;
    description: string | null;
    discord_webhook_url: string | null;
    created_at: string;
    role: 'owner' | 'editor' | 'viewer'; // ProjectMemberからの結合データ
}

export const dashboardApi = {
    getProjects: async (): Promise<Project[]> => {
        const response = await apiClient.get<Project[]>('/projects');
        return response.data;
    },

    createProject: async (data: { name: string; description?: string }): Promise<Project> => {
        const response = await apiClient.post<Project>('/projects', data);
        return response.data;
    },
};
