import { apiClient } from '@/api/client';
import type { Script, ScriptSummary } from '@/types';

interface ScriptListResponse {
    scripts: ScriptSummary[];
}

export const scriptsApi = {
    getScripts: async (projectId: string): Promise<ScriptSummary[]> => {
        const response = await apiClient.get<ScriptListResponse>(`/scripts/${projectId}`);
        return response.data.scripts;
    },

    uploadScript: async (projectId: string, formData: FormData): Promise<Script> => {
        const response = await apiClient.post<Script>(`/scripts/${projectId}/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getScript: async (projectId: string, scriptId: string): Promise<Script> => {
        const response = await apiClient.get<Script>(`/scripts/${projectId}/${scriptId}`);
        return response.data;
    },

    deleteScript: async (projectId: string, scriptId: string): Promise<void> => {
        await apiClient.delete(`/scripts/${projectId}/${scriptId}`);
    },

    downloadScriptPdf: async (projectId: string, scriptId: string): Promise<Blob> => {
        const response = await apiClient.get(`/scripts/${projectId}/${scriptId}/pdf`, {
            responseType: 'blob',
        });
        return response.data;
    },

    updatePublicity: async (scriptId: string, isPublic: boolean): Promise<void> => {
        const formData = new FormData();
        formData.append('is_public', String(isPublic));
        await apiClient.patch(`/scripts/${scriptId}/publicity`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    }
};
