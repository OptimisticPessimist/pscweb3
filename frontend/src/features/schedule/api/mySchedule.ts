import { apiClient } from '@/api/client';

export interface MyScheduleEvent {
    id: string;
    title: string;
    start: string;
    end: string | null;
    type: 'rehearsal' | 'milestone';
    project_id: string;
    project_name: string;
    project_color: string;
    location: string | null;
    notes: string | null;
    scene_heading: string | null;
}

export interface MyScheduleResponse {
    events: MyScheduleEvent[];
}

export const myScheduleApi = {
    getMySchedule: async (): Promise<MyScheduleResponse> => {
        const response = await apiClient.get('/my-schedule');
        return response.data;
    }
};
