import { apiClient } from '@/api/client';
import type { Project, ProjectMember } from '@/types';

export const projectsApi = {
    async getProject(id: string): Promise<Project> {
        const response = await apiClient.get(`/projects/${id}`);
        return response.data;
    },

    async getProjectMembers(id: string): Promise<ProjectMember[]> {
        const response = await apiClient.get(`/projects/${id}/members`);
        return response.data;
    },

    async updateMemberRole(projectId: string, userId: string, role: string, defaultStaffRole?: string | null, displayName?: string | null): Promise<ProjectMember> {
        const response = await apiClient.put(`/projects/${projectId}/members/${userId}`, {
            role,
            default_staff_role: defaultStaffRole,
            display_name: displayName,
        });
        return response.data;
    },

    async deleteMember(projectId: string, userId: string): Promise<void> {
        await apiClient.delete(`/projects/${projectId}/members/${userId}`);
    },
};
