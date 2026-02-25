import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { schedulePollApi } from '../api/schedulePoll';
import {
    Clock,
    CheckCircle2,
    HelpCircle,
    XCircle,
    ChevronLeft,
    Sparkles,
    Check,
    ArrowRight,
    User
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHead } from '@/components/PageHead';
import { useAuth } from '@/features/auth/hooks/useAuth';
import toast from 'react-hot-toast';

export const SchedulePollDetailPage: React.FC = () => {
    const { t } = useTranslation();
    const { projectId, pollId } = useParams<{ projectId: string, pollId: string }>();
    const navigate = useNavigate();
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const [selectedCandidateForFinalize, setSelectedCandidateForFinalize] = useState<string | null>(null);

    const { data: poll, isLoading } = useQuery({
        queryKey: ['schedulePoll', projectId, pollId],
        queryFn: () => schedulePollApi.getPoll(projectId!, pollId!),
        enabled: !!projectId && !!pollId,
    });

    const { data: recommendations } = useQuery({
        queryKey: ['schedulePollRecommendations', projectId, pollId],
        queryFn: () => schedulePollApi.getRecommendations(projectId!, pollId!),
        enabled: !!projectId && !!pollId,
    });

    const answerMutation = useMutation({
        mutationFn: ({ candidateId, status }: { candidateId: string, status: 'ok' | 'maybe' | 'ng' }) =>
            schedulePollApi.answerPoll(projectId!, pollId!, candidateId, status),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['schedulePoll', projectId, pollId] });
            toast.success(t('schedulePoll.answerSaved') || '回答を保存しました');
        },
    });

    const finalizeMutation = useMutation({
        mutationFn: ({ candidateId, sceneIds }: { candidateId: string, sceneIds: string[] }) =>
            schedulePollApi.finalizePoll(projectId!, pollId!, candidateId, sceneIds),
        onSuccess: () => {
            toast.success(t('schedulePoll.finalized') || '稽古予定を作成しました');
            navigate(`/projects/${projectId}/schedule`);
        },
    });

    // 参加者のユニークリストを作成（グリッドの列用）
    const participants = useMemo(() => {
        if (!poll) return [];
        const userMap = new Map<string, { id: string, name: string }>();
        poll.candidates.forEach(c => {
            c.answers.forEach(a => {
                if (!userMap.has(a.user_id)) {
                    userMap.set(a.user_id, {
                        id: a.user_id,
                        name: a.display_name || a.discord_username || 'Unknown'
                    });
                }
            });
        });
        return Array.from(userMap.values());
    }, [poll]);

    if (isLoading || !poll) {
        return (
            <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    const getStatusIcon = (status: 'ok' | 'maybe' | 'ng' | undefined) => {
        switch (status) {
            case 'ok': return <CheckCircle2 className="h-6 w-6 text-emerald-500" />;
            case 'maybe': return <HelpCircle className="h-6 w-6 text-amber-500" />;
            case 'ng': return <XCircle className="h-6 w-6 text-rose-500" />;
            default: return <div className="h-6 w-6 border-2 border-dashed border-gray-200 rounded-full" />;
        }
    };

    return (
        <div className="p-6 space-y-8 animate-in fade-in duration-500">
            <PageHead title={poll.title} />

            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => navigate(`/projects/${projectId}/polls`)}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <ChevronLeft className="h-6 w-6 text-gray-600" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">{poll.title}</h1>
                        <p className="text-gray-500 mt-1">{poll.description}</p>
                    </div>
                </div>
            </div>

            {/* おすすめ日程セクション */}
            {recommendations && recommendations.length > 0 && (
                <section className="bg-violet-50/50 border border-violet-100 rounded-2xl p-6 shadow-sm">
                    <div className="flex items-center space-x-2 mb-4">
                        <Sparkles className="h-5 w-5 text-violet-600" />
                        <h2 className="text-lg font-bold text-violet-900">{t('schedulePoll.recommendations') || 'システムによるおすすめ日程'}</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {recommendations.slice(0, 3).map((rec, idx) => (
                            <div key={rec.candidate_id} className="bg-white border border-violet-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                                <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                                    <Sparkles className="h-12 w-12 text-violet-600" />
                                </div>
                                <div className="text-xs font-bold text-violet-600 mb-1 uppercase tracking-wider">Rank #{idx + 1}</div>
                                <div className="text-sm font-bold text-gray-900 mb-1">
                                    {new Date(rec.start_datetime).toLocaleDateString(undefined, { month: 'short', day: 'numeric', weekday: 'short' })}
                                </div>
                                <div className="text-xs text-gray-500 mb-2 flex items-center">
                                    <Clock className="h-3 w-3 mr-1" />
                                    {new Date(rec.start_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                    {' - '}
                                    {new Date(rec.end_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                </div>

                                {rec.reason && (
                                    <div className="mb-3">
                                        <div className="text-[10px] font-bold text-violet-500 uppercase tracking-tighter mb-0.5">Recommendation Reason</div>
                                        <div className="text-xs text-violet-900 bg-violet-50 px-2 py-1 rounded border border-violet-100 font-medium">
                                            {rec.reason}
                                        </div>
                                    </div>
                                )}

                                <div className="mb-4">
                                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter mb-1">Possible Scenes</div>
                                    <div className="space-y-1">
                                        {rec.possible_scenes.map((ps: any) => (
                                            <div key={ps.scene_id} className="text-[11px] text-gray-700 flex items-center bg-gray-50/50 px-1.5 py-0.5 rounded">
                                                <span className="font-bold mr-1">#{ps.scene_number}</span>
                                                <span className="truncate">{ps.scene_heading}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <button
                                    onClick={() => setSelectedCandidateForFinalize(rec.candidate_id)}
                                    className="w-full py-2 bg-violet-600 text-white text-xs font-bold rounded-lg hover:bg-violet-700 transition-colors flex items-center justify-center"
                                >
                                    {t('schedulePoll.finalizeThis') || 'この日で確定する'}
                                    <ArrowRight className="h-3 w-3 ml-2" />
                                </button>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* 回答グリッド */}
            <div className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50/50 border-b border-gray-100">
                                <th className="px-6 py-5 text-sm font-bold text-gray-700 w-64 sticky left-0 bg-white z-10 backdrop-blur-sm shadow-[1px_0_0_0_rgba(0,0,0,0.05)]">
                                    {t('schedulePoll.dateColumn') || '候補日時'}
                                </th>
                                {participants.map(p => (
                                    <th key={p.id} className="px-6 py-5 text-sm font-bold text-gray-700 text-center min-w-[120px]">
                                        <div className="flex flex-col items-center">
                                            <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center mb-1">
                                                <User className="h-4 w-4 text-indigo-600" />
                                            </div>
                                            <span className="truncate max-w-[100px]">{p.name}</span>
                                        </div>
                                    </th>
                                ))}
                                <th className="px-6 py-5 text-sm font-bold text-gray-700 text-center min-w-[150px]">
                                    {t('schedulePoll.myAnswer') || 'あなたの回答'}
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {poll.candidates.map((candidate) => {
                                const myAnswer = candidate.answers.find(a => a.user_id === user?.id)?.status;
                                return (
                                    <tr key={candidate.id} className="hover:bg-gray-50/50 transition-colors group">
                                        <td className="px-6 py-5 sticky left-0 bg-white group-hover:bg-gray-50/50 z-10 backdrop-blur-sm shadow-[1px_0_0_0_rgba(0,0,0,0.05)]">
                                            <div className="text-sm font-bold text-gray-900">
                                                {new Date(candidate.start_datetime).toLocaleDateString(undefined, { month: 'short', day: 'numeric', weekday: 'short' })}
                                            </div>
                                            <div className="text-xs text-gray-500 flex items-center mt-1">
                                                <Clock className="h-3 w-3 mr-1" />
                                                {new Date(candidate.start_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                                {' - '}
                                                {new Date(candidate.end_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                            </div>
                                        </td>
                                        {participants.map(p => {
                                            const status = candidate.answers.find(a => a.user_id === p.id)?.status;
                                            return (
                                                <td key={p.id} className="px-6 py-5 text-center">
                                                    <div className="flex justify-center">
                                                        {getStatusIcon(status)}
                                                    </div>
                                                </td>
                                            );
                                        })}
                                        <td className="px-6 py-5">
                                            <div className="flex justify-center items-center space-x-2">
                                                <button
                                                    onClick={() => answerMutation.mutate({ candidateId: candidate.id, status: 'ok' })}
                                                    className={`p-2 rounded-lg transition-all ${myAnswer === 'ok' ? 'bg-emerald-100 scale-110 shadow-sm' : 'hover:bg-emerald-50'}`}
                                                >
                                                    <CheckCircle2 className={`h-6 w-6 ${myAnswer === 'ok' ? 'text-emerald-600' : 'text-gray-300'}`} />
                                                </button>
                                                <button
                                                    onClick={() => answerMutation.mutate({ candidateId: candidate.id, status: 'maybe' })}
                                                    className={`p-2 rounded-lg transition-all ${myAnswer === 'maybe' ? 'bg-amber-100 scale-110 shadow-sm' : 'hover:bg-amber-50'}`}
                                                >
                                                    <HelpCircle className={`h-6 w-6 ${myAnswer === 'maybe' ? 'text-amber-600' : 'text-gray-300'}`} />
                                                </button>
                                                <button
                                                    onClick={() => answerMutation.mutate({ candidateId: candidate.id, status: 'ng' })}
                                                    className={`p-2 rounded-lg transition-all ${myAnswer === 'ng' ? 'bg-rose-100 scale-110 shadow-sm' : 'hover:bg-rose-50'}`}
                                                >
                                                    <XCircle className={`h-6 w-6 ${myAnswer === 'ng' ? 'text-rose-600' : 'text-gray-300'}`} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 確定用モーダル（簡易版） */}
            {selectedCandidateForFinalize && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm overflow-y-auto">
                    <div className="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl animate-in zoom-in duration-300">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-3 bg-violet-100 rounded-2xl">
                                <Sparkles className="h-6 w-6 text-violet-600" />
                            </div>
                            <h2 className="text-xl font-bold text-gray-900">{t('schedulePoll.finalizeTitle') || '予定を確定する'}</h2>
                        </div>

                        <div className="p-4 bg-gray-50 rounded-2xl mb-6">
                            <div className="text-sm font-bold text-gray-900">
                                {new Date(poll.candidates.find(c => c.id === selectedCandidateForFinalize)?.start_datetime || '').toLocaleDateString(undefined, { month: 'long', day: 'numeric', weekday: 'long' })}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                                {new Date(poll.candidates.find(c => c.id === selectedCandidateForFinalize)?.start_datetime || '').toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                {' - '}
                                {new Date(poll.candidates.find(c => c.id === selectedCandidateForFinalize)?.end_datetime || '').toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                            </div>
                        </div>

                        <p className="text-sm text-gray-500 mb-8 leading-relaxed">
                            {t('schedulePoll.finalizeConfirm') || 'この日程で稽古予定を作成します。紐付けるシーンはおすすめに含まれるものが自動的に選択されますが、詳細は後の画面で調整可能です。'}
                        </p>

                        <div className="flex space-x-3">
                            <button
                                onClick={() => setSelectedCandidateForFinalize(null)}
                                className="flex-1 py-3 border border-gray-200 text-gray-700 font-bold rounded-xl hover:bg-gray-50 transition-colors"
                            >
                                {t('common.cancel')}
                            </button>
                            <button
                                onClick={() => {
                                    const rec = recommendations?.find(r => r.candidate_id === selectedCandidateForFinalize);
                                    finalizeMutation.mutate({
                                        candidateId: selectedCandidateForFinalize,
                                        sceneIds: rec?.possible_scenes.map(s => s.scene_id) || []
                                    });
                                }}
                                disabled={finalizeMutation.isPending}
                                className="flex-1 py-3 bg-violet-600 text-white font-bold rounded-xl hover:bg-violet-700 transition-colors shadow-lg shadow-violet-200 flex items-center justify-center disabled:opacity-50"
                            >
                                {finalizeMutation.isPending ? '...' : (t('common.confirm') || '確定する')}
                                <Check className="h-4 w-4 ml-2" />
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
