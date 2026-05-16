import { apiClient } from '@/api/client';
import type { Script, ScriptSummary } from '@/types';

interface ScriptListResponse {
    scripts: ScriptSummary[];
}

interface ImportedProjectResponse {
    id: string;
    scripts?: Array<{ id: string }>;
}

export const scriptsApi = {
    getScripts: async (projectId: string): Promise<ScriptSummary[]> => {
        const response = await apiClient.get<ScriptListResponse>(`/scripts/${projectId}`);
        return response.data.scripts;
    },

    uploadScript: async (projectId: string, formData: FormData): Promise<Script> => {
        const response = await apiClient.post<Script>(`/scripts/${projectId}/upload`, formData);
        return response.data;
    },

    getScript: async (projectId: string, scriptId: string): Promise<Script> => {
        const response = await apiClient.get<Script>(`/scripts/${projectId}/${scriptId}`);
        return response.data;
    },

    deleteScript: async (projectId: string, scriptId: string): Promise<void> => {
        void scriptId;
        await apiClient.delete(`/scripts/${projectId}/scripts`);
    },

    downloadScriptPdf: async (
        projectId: string,
        scriptId: string,
        options?: { orientation?: string; writingDirection?: string }
    ): Promise<Blob> => {
        const params = new URLSearchParams();
        if (options?.orientation) params.append('orientation', options.orientation);
        if (options?.writingDirection) params.append('writing_direction', options.writingDirection);
        const query = params.toString() ? `?${params.toString()}` : '';
        const response = await apiClient.get(`/scripts/${projectId}/${scriptId}/pdf${query}`, {
            responseType: 'blob',
        });
        return response.data;
    },

    updatePublicity: async (scriptId: string, isPublic: boolean): Promise<void> => {
        const formData = new FormData();
        formData.append('is_public', String(isPublic));
        await apiClient.patch(`/scripts/${scriptId}/publicity`, formData);
    },

    getPublicScript: async (scriptId: string): Promise<Script> => {
        const response = await apiClient.get<Script>(`/public/scripts/${scriptId}`);
        return response.data;
    },

    importScript: async (scriptId: string): Promise<ImportedProjectResponse> => {
        const response = await apiClient.post<ImportedProjectResponse>(`/projects/import-script/${scriptId}`);
        return response.data;
    },

    // 脚本リセット（脚本由来データを削除、カスタムデータは保持）
    resetScript: async (projectId: string): Promise<void> => {
        await apiClient.delete(`/scripts/${projectId}/scripts`);
    },
};
