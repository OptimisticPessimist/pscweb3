import { apiClient } from '@/api/client';
import type { CharacterWithCastings, CastingUser } from '@/types';

export const charactersApi = {
    // キャラクタ一覧（キャスト情報込み）取得
    getCharacters: async (projectId: string): Promise<CharacterWithCastings[]> => {
        const response = await apiClient.get(`/projects/${projectId}/characters`);
        return response.data;
    },

    // キャスト追加
    addCasting: async (projectId: string, characterId: string, userId: string, castName?: string): Promise<CastingUser[]> => {
        const response = await apiClient.post(`/projects/${projectId}/characters/${characterId}/cast`, {
            user_id: userId,
            cast_name: castName,
        });
        return response.data;
    },

    // キャスト削除
    removeCasting: async (projectId: string, characterId: string, userId: string): Promise<CastingUser[]> => {
        const response = await apiClient.delete(`/projects/${projectId}/characters/${characterId}/cast/${userId}`);
        return response.data;
    },
};
