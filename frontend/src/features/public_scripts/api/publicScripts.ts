import { apiClient } from '@/api/client';
import type { Script } from '@/types';

export interface PublicScriptResponse {
    scripts: Script[];
}

export const publicScriptsApi = {
    getPublicScripts: async (limit = 20, offset = 0): Promise<PublicScriptResponse> => {
        const response = await apiClient.get('/public/scripts', {
            params: { limit, offset },
        });
        return response.data;
    },

    getPublicScript: async (scriptId: string): Promise<Script> => {
        const response = await apiClient.get(`/public/scripts/${scriptId}`);
        return response.data;
    },
};
