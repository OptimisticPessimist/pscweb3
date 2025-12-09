import { apiClient } from '@/api/client';
import type { InvitationCreate, InvitationResponse, InvitationAcceptResponse } from '@/types';

export const invitationsApi = {
    async createInvitation(projectId: string, data: InvitationCreate): Promise<InvitationResponse> {
        const response = await apiClient.post(`/invitations/projects/${projectId}/invitations`, data);
        return response.data;
    },

    async getInvitation(token: string): Promise<InvitationResponse> {
        const response = await apiClient.get(`/invitations/invitations/${token}`);
        return response.data;
    },

    async acceptInvitation(token: string): Promise<InvitationAcceptResponse> {
        const response = await apiClient.post(`/invitations/invitations/${token}/accept`);
        return response.data;
    },
};
