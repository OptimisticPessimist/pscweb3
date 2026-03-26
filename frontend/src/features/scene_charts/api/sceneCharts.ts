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

    // 手動マッピング追加
    addMapping: async (projectId: string, sceneId: string, characterId: string): Promise<void> => {
        await apiClient.post(`/projects/${projectId}/scene-chart/mappings`, {
            scene_id: sceneId,
            character_id: characterId,
        });
    },

    // 手動マッピング削除
    removeMapping: async (projectId: string, sceneId: string, characterId: string): Promise<void> => {
        await apiClient.delete(`/projects/${projectId}/scene-chart/mappings`, {
            data: {
                scene_id: sceneId,
                character_id: characterId,
            },
        });
    },

    // カスタムシーン追加
    createScene: async (projectId: string, data: { heading: string; act_number?: number | null; scene_number: number }): Promise<{ id: string }> => {
        const response = await apiClient.post(`/projects/${projectId}/scenes`, data);
        return response.data;
    },

    // カスタムシーン削除
    deleteScene: async (projectId: string, sceneId: string): Promise<void> => {
        await apiClient.delete(`/projects/${projectId}/scenes/${sceneId}`);
    },

    // シーン編集
    updateScene: async (projectId: string, sceneId: string, data: { heading?: string; act_number?: number | null; scene_number?: number }): Promise<void> => {
        await apiClient.patch(`/projects/${projectId}/scenes/${sceneId}`, data);
    },
};
