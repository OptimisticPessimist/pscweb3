import { apiClient } from '@/api/client';
import type { RehearsalScheduleResponse, RehearsalResponse, RehearsalCreate, RehearsalUpdate } from '@/types';

// TODO: Define these types in src/types/index.ts if not already present
// For now, I'll assume they will be added there.
// If not, I can define temporary interfaces here or update index.ts.

export const rehearsalsApi = {
    async getSchedule(projectId: string): Promise<RehearsalScheduleResponse> {
        const response = await apiClient.get(`/projects/${projectId}/rehearsal-schedule`);
        return response.data;
    },

    async createSchedule(projectId: string, scriptId: string): Promise<RehearsalScheduleResponse> {
        const response = await apiClient.post(`/projects/${projectId}/rehearsal-schedule`, null, {
            params: { script_id: scriptId }
        });
        return response.data;
    },

    async addRehearsal(scheduleId: string, data: RehearsalCreate): Promise<RehearsalResponse> {
        const response = await apiClient.post(`/schedules/${scheduleId}/rehearsals`, data);
        return response.data;
    },

    async updateRehearsal(rehearsalId: string, data: RehearsalUpdate): Promise<RehearsalResponse> {
        const response = await apiClient.put(`/rehearsals/${rehearsalId}`, data);
        return response.data;
    },

    async deleteRehearsal(rehearsalId: string): Promise<void> {
        await apiClient.delete(`/rehearsals/${rehearsalId}`);
    },

    async addParticipant(rehearsalId: string, userId: string): Promise<void> {
        await apiClient.post(`/rehearsals/${rehearsalId}/participants/${userId}`);
    },

    async deleteParticipant(rehearsalId: string, userId: string): Promise<void> {
        await apiClient.delete(`/rehearsals/${rehearsalId}/participants/${userId}`);
    },

    async updateParticipantRole(rehearsalId: string, userId: string, role: string | null): Promise<void> {
        await apiClient.put(`/rehearsals/${rehearsalId}/participants/${userId}`, { staff_role: role });
    },

    async addCast(rehearsalId: string, characterId: string, userId: string): Promise<void> {
        await apiClient.post(`/rehearsals/${rehearsalId}/casts`, { character_id: characterId, user_id: userId });
    },

    async deleteCast(rehearsalId: string, characterId: string): Promise<void> {
        await apiClient.delete(`/rehearsals/${rehearsalId}/casts/${characterId}`);
    }
};
