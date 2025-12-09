import { apiClient } from '@/api/client';
import type { SceneChart } from '@/types';

export const sceneChartsApi = {
    // 香盤表の自動生成
    generateSceneChart: async (scriptId: string): Promise<SceneChart> => {
        const response = await apiClient.post<SceneChart>(`/scripts/${scriptId}/generate-scene-chart`);
        return response.data;
    },

    // 香盤表の取得
    getSceneChart: async (scriptId: string): Promise<SceneChart> => {
        const response = await apiClient.get<SceneChart>(`/scripts/${scriptId}/scene-chart`);
        return response.data;
    },
};
