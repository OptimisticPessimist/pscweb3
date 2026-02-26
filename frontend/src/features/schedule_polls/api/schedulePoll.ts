import { apiClient } from '@/api/client';

export interface SchedulePollAnswerResponse {
    user_id: string;
    display_name: string | null;
    discord_username: string | null;
    status: 'ok' | 'maybe' | 'ng';
    role?: string;
}

export interface SchedulePollCandidateResponse {
    id: string;
    poll_id: string;
    start_datetime: string;
    end_datetime: string;
    answers: SchedulePollAnswerResponse[];
}

export interface SchedulePollResponse {
    id: string;
    project_id: string;
    title: string;
    description: string | null;
    is_closed: boolean;
    created_at: string;
    creator_id: string;
    required_roles: string | null;
    candidates: SchedulePollCandidateResponse[];
}

export interface RecommendationScene {
    scene_id: string;
    scene_number: number;
    scene_heading: string;
    score: number;
    reason: string;
}

export interface ScheduleRecommendation {
    candidate_id: string;
    start_datetime: string;
    end_datetime: string;
    possible_scenes: RecommendationScene[];
    reason: string;
}

export interface SceneAvailability {
    scene_id: string;
    scene_number: number;
    heading: string;
    is_possible: boolean;
    is_reach: boolean;
    missing_user_names: string[];
    reason: string | null;
}

export interface PollCandidateAnalysis {
    candidate_id: string;
    start_datetime: string;
    end_datetime: string;
    possible_scenes: SceneAvailability[];
    reach_scenes: SceneAvailability[];
    available_users: string[];
    maybe_users: string[];
}

export interface SchedulePollCalendarAnalysis {
    poll_id: string;
    analyses: PollCandidateAnalysis[];
}

export const schedulePollApi = {
    // 日程調整一覧を取得
    getPolls: async (projectId: string): Promise<SchedulePollResponse[]> => {
        const response = await apiClient.get<SchedulePollResponse[]>(`/projects/${projectId}/polls`);
        return response.data;
    },

    // 日程調整詳細を取得
    getPoll: async (projectId: string, poll_id: string): Promise<SchedulePollResponse> => {
        const response = await apiClient.get<SchedulePollResponse>(`/projects/${projectId}/polls/${poll_id}`);
        return response.data;
    },

    // カレンダー分析を取得
    getCalendarAnalysis: async (projectId: string, poll_id: string): Promise<SchedulePollCalendarAnalysis> => {
        const response = await apiClient.get<SchedulePollCalendarAnalysis>(`/projects/${projectId}/polls/${poll_id}/calendar-analysis`);
        return response.data;
    },

    // 回答を送信
    answerPoll: async (projectId: string, poll_id: string, candidate_id: string, status: 'ok' | 'maybe' | 'ng'): Promise<void> => {
        await apiClient.post(`/projects/${projectId}/polls/${poll_id}/candidates/${candidate_id}/answer`, { status });
    },

    // おすすめを取得
    getRecommendations: async (projectId: string, poll_id: string): Promise<ScheduleRecommendation[]> => {
        const response = await apiClient.get<ScheduleRecommendation[]>(`/projects/${projectId}/polls/${poll_id}/recommendations`);
        return response.data;
    },

    // 日程を確定
    finalizePoll: async (projectId: string, poll_id: string, candidate_id: string, scene_ids: string[]): Promise<void> => {
        await apiClient.post(`/projects/${projectId}/polls/${poll_id}/finalize`, { candidate_id, scene_ids });
    },

    // 日程調整を作成
    createPoll: async (projectId: string, data: {
        title: string,
        description?: string,
        required_roles?: string[],
        candidates: { start_datetime: string, end_datetime: string }[]
    }): Promise<SchedulePollResponse> => {
        const response = await apiClient.post<SchedulePollResponse>(`/projects/${projectId}/polls`, data);
        return response.data;
    },

    // 日程調整を削除
    deletePoll: async (projectId: string, pollId: string): Promise<void> => {
        await apiClient.delete(`/projects/${projectId}/polls/${pollId}`);
    }
};
