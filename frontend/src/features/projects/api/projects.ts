import { apiClient } from '@/api/client';
import type { Project, ProjectMember } from '@/types';

export const projectsApi = {
    async getProject(id: string): Promise<Project> {
        const response = await apiClient.get(`/projects/${id}`);
        return response.data;
    },

    async updateProject(id: string, data: Partial<Project>): Promise<Project> {
        const response = await apiClient.put(`/projects/${id}`, data);
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

    async getMilestones(projectId: string): Promise<import('@/types').Milestone[]> {
        const response = await apiClient.get(`/projects/${projectId}/milestones`);
        return response.data;
    },

    async createMilestone(projectId: string, data: import('@/types').MilestoneCreate): Promise<import('@/types').Milestone> {
        const response = await apiClient.post(`/projects/${projectId}/milestones`, data);
        return response.data;
    },

    async updateMilestone(projectId: string, milestoneId: string, data: Partial<import('@/types').MilestoneCreate>): Promise<import('@/types').Milestone> {
        const response = await apiClient.patch(`/projects/${projectId}/milestones/${milestoneId}`, data);
        return response.data;
    },

    async deleteMilestone(projectId: string, milestoneId: string): Promise<void> {
        await apiClient.delete(`/projects/${projectId}/milestones/${milestoneId}`);
    },
};
