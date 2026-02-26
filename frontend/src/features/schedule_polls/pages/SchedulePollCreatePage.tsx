import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { schedulePollApi } from '../api/schedulePoll';
import { projectsApi } from '@/features/projects/api/projects';
import {
    Calendar,
    Clock,
    Plus,
    Trash2,
    ChevronLeft,
    Send,
    Shield,
    Users
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHead } from '@/components/PageHead';
import toast from 'react-hot-toast';

interface DateCandidate {
    start_date: string;
    start_time: string;
    end_time: string;
}

export const SchedulePollCreatePage: React.FC = () => {
    const { t } = useTranslation();
    const { projectId } = useParams<{ projectId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [requiredRoles, setRequiredRoles] = useState<string[]>([]);
    const [candidates, setCandidates] = useState<DateCandidate[]>([
        { start_date: '', start_time: '18:00', end_time: '21:00' }
    ]);

    const { data: members } = useQuery({
        queryKey: ['projectMembers', projectId],
        queryFn: () => projectsApi.getProjectMembers(projectId!),
        enabled: !!projectId
    });

    const roles = React.useMemo(() => {
        if (!members) return [];
        const uniqueRoles = new Set<string>();
        members.forEach(m => {
            if (m.default_staff_role) uniqueRoles.add(m.default_staff_role);
        });
        return Array.from(uniqueRoles).sort();
    }, [members]);

    const createMutation = useMutation({
        mutationFn: (data: { title: string, description?: string, required_roles?: string[], candidates: { start_datetime: string, end_datetime: string }[] }) =>
            schedulePollApi.createPoll(projectId!, data),
        onSuccess: (newPoll) => {
            queryClient.invalidateQueries({ queryKey: ['schedulePolls', projectId] });
            toast.success(t('schedulePoll.created') || '日程調整を作成しました');
            navigate(`/projects/${projectId}/polls/${newPoll.id}`);
        },
        onError: (error) => {
            console.error('Create poll failed:', error);
            toast.error(t('schedulePoll.createError') || '日程調整の作成に失敗しました');
        }
    });

    const addCandidate = () => {
        const last = candidates[candidates.length - 1];
        setCandidates([...candidates, {
            start_date: last?.start_date || '',
            start_time: last?.start_time || '18:00',
            end_time: last?.end_time || '21:00'
        }]);
    };

    const removeCandidate = (index: number) => {
        if (candidates.length > 1) {
            setCandidates(candidates.filter((_, i) => i !== index));
        }
    };

    const updateCandidate = (index: number, field: keyof DateCandidate, value: string) => {
        const newCandidates = [...candidates];
        newCandidates[index] = { ...newCandidates[index], [field]: value };
        setCandidates(newCandidates);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!title) {
            toast.error(t('schedulePoll.titleRequired') || 'タイトルを入力してください');
            return;
        }

        const formattedCandidates = candidates
            .filter(c => c.start_date && c.start_time && c.end_time)
            .map(c => ({
                // ブラウザのローカル時間としてパースしてからUTCに変換する
                start_datetime: new Date(`${c.start_date}T${c.start_time}:00`).toISOString(),
                end_datetime: new Date(`${c.start_date}T${c.end_time}:00`).toISOString()
            }));

        if (formattedCandidates.length === 0) {
            toast.error(t('schedulePoll.atLeastOneCandidate') || '少なくとも1つの候補日を正しく入力してください');
            return;
        }

        createMutation.mutate({
            title,
            description,
            required_roles: requiredRoles,
            candidates: formattedCandidates
        });
    };

    const toggleRole = (role: string) => {
        if (requiredRoles.includes(role)) {
            setRequiredRoles(requiredRoles.filter(r => r !== role));
        } else {
            setRequiredRoles([...requiredRoles, role]);
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-8 animate-in slide-in-from-bottom-4 duration-500">
            <PageHead title={t('schedulePoll.createTitle') || '新しい日程調整'} />

            <div className="flex items-center space-x-4">
                <button
                    onClick={() => navigate(`/projects/${projectId}/polls`)}
                    className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                    <ChevronLeft className="h-6 w-6 text-gray-600" />
                </button>
                <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
                    {t('schedulePoll.createTitle') || '新しい日程調整'}
                </h1>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-8 space-y-6">
                    <div>
                        <label htmlFor="title" className="block text-sm font-bold text-gray-700 mb-2">
                            {t('schedulePoll.titleLabel') || 'タイトル'}
                        </label>
                        <input
                            id="title"
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder={t('schedulePoll.titlePlaceholder') || '例：10月後半の抜き稽古'}
                            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="description" className="block text-sm font-bold text-gray-700 mb-2">
                            {t('schedulePoll.descriptionLabel') || '説明（任意）'}
                        </label>
                        <textarea
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                            placeholder={t('schedulePoll.descriptionPlaceholder') || '回答期限や、調整の目的などを入力してください'}
                            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                        />
                    </div>

                    {roles.length > 0 && (
                        <div>
                            <label className="flex items-center text-sm font-bold text-gray-700 mb-3">
                                <Shield className="h-4 w-4 mr-2 text-indigo-500" />
                                {t('schedulePoll.requiredRolesLabel') || '出席必須の役職（任意）'}
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {roles.map(role => (
                                    <button
                                        key={role}
                                        type="button"
                                        onClick={() => toggleRole(role)}
                                        className={`px-4 py-2 rounded-xl text-sm font-bold transition-all border ${requiredRoles.includes(role)
                                                ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-100'
                                                : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'
                                            }`}
                                    >
                                        {role}
                                    </button>
                                ))}
                            </div>
                            <p className="text-xs text-gray-400 mt-2 flex items-center">
                                <Users className="h-3 w-3 mr-1" />
                                {t('schedulePoll.requiredRolesHint') || '選択した役職のメンバーが全員 NG の日程は「稽古不可」として判定されます。'}
                            </p>
                        </div>
                    )}
                </div>

                <div className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-8">
                    <div className="flex justify-between items-center mb-6">
                        <label className="block text-sm font-bold text-gray-700">
                            {t('schedulePoll.candidatesLabel') || '候補日時'}
                        </label>
                        <button
                            type="button"
                            onClick={addCandidate}
                            className="text-sm font-bold text-indigo-600 hover:text-indigo-700 flex items-center bg-indigo-50 px-3 py-2 rounded-lg transition-colors"
                        >
                            <Plus className="h-4 w-4 mr-1" />
                            {t('schedulePoll.addCandidate') || '追加'}
                        </button>
                    </div>

                    <div className="space-y-4">
                        {candidates.map((candidate, index) => (
                            <div key={index} className="flex items-center space-x-3 animate-in fade-in slide-in-from-left-2 duration-300" style={{ animationDelay: `${index * 50}ms` }}>
                                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div className="relative">
                                        <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                        <input
                                            type="date"
                                            value={candidate.start_date}
                                            onChange={(e) => updateCandidate(index, 'start_date', e.target.value)}
                                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-sm"
                                            required
                                        />
                                    </div>
                                    <div className="relative">
                                        <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                        <input
                                            type="time"
                                            value={candidate.start_time}
                                            onChange={(e) => updateCandidate(index, 'start_time', e.target.value)}
                                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-sm"
                                            required
                                        />
                                    </div>
                                    <div className="relative">
                                        <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                        <input
                                            type="time"
                                            value={candidate.end_time}
                                            onChange={(e) => updateCandidate(index, 'end_time', e.target.value)}
                                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-sm"
                                            required
                                        />
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => removeCandidate(index)}
                                    disabled={candidates.length === 1}
                                    className="p-3 text-gray-400 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all disabled:opacity-30 disabled:hover:bg-transparent"
                                >
                                    <Trash2 className="h-5 w-5" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="flex justify-end pt-4">
                    <button
                        type="submit"
                        disabled={createMutation.isPending}
                        className="px-10 py-4 bg-indigo-600 text-white font-bold rounded-2xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 flex items-center transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
                    >
                        {createMutation.isPending ? '...' : (t('schedulePoll.submitCreate') || '日程調整を作成・Discord送信')}
                        <Send className="h-5 w-5 ml-2" />
                    </button>
                </div>
            </form>
        </div>
    );
};
