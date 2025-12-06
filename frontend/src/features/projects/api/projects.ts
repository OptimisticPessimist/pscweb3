import { apiClient } from '@/api/client';
import type { Project } from '@/types';

export const projectsApi = {
    getProject: async (id: string): Promise<Project> => {
        const response = await apiClient.get(`/projects/${id}`);
        return response.data;
    },

    // 他のメソッドは必要に応じて追加
    // updateProject, deleteProject, etc.
};
