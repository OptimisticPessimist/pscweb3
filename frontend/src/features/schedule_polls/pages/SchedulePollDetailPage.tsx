import React, { useState, useMemo, useEffect } from 'react';
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
    User,
    Trash2,
    Calendar,
    LayoutGrid,
    Shield,
    Bell,
    UserCheck,
    UserMinus,
    RefreshCw
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHead } from '@/components/PageHead';
import { useAuth } from '@/features/auth/hooks/useAuth';
import toast from 'react-hot-toast';
import { SchedulePollCalendar } from '../components/SchedulePollCalendar';

export const SchedulePollDetailPage: React.FC = () => {
    const { t } = useTranslation();
    const { projectId, pollId } = useParams<{ projectId: string, pollId: string }>();
    const navigate = useNavigate();
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const [selectedCandidateForFinalize, setSelectedCandidateForFinalize] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'grid' | 'calendar'>('grid');

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

    const { data: analysis } = useQuery({
        queryKey: ['schedulePollAnalysis', projectId, pollId],
        queryFn: () => schedulePollApi.getCalendarAnalysis(projectId!, pollId!),
        enabled: !!projectId && !!pollId && viewMode === 'calendar',
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

    const deleteMutation = useMutation({
        mutationFn: () => schedulePollApi.deletePoll(projectId!, pollId!),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['schedulePolls', projectId] });
            toast.success(t('schedulePoll.deleted') || '日程調整を削除しました');
            navigate(`/projects/${projectId}/polls`);
        },
        onError: () => {
            toast.error(t('schedulePoll.deleteFailed') || '削除に失敗しました（権限が不足している可能性があります）');
        }
    });

    const [targetUserIds, setTargetUserIds] = useState<string[]>([]);

    const { data: unansweredMembers, refetch: refetchUnanswered } = useQuery({
        queryKey: ['schedulePollUnanswered', projectId, pollId],
        queryFn: () => schedulePollApi.getUnansweredMembers(projectId!, pollId!),
        enabled: !!projectId && !!pollId,
    });

    useEffect(() => {
        if (unansweredMembers) {
            setTargetUserIds(unansweredMembers.map(m => m.user_id));
        }
    }, [unansweredMembers]);

    const remindMutation = useMutation({
        mutationFn: () => schedulePollApi.remindUnansweredMembers(projectId!, pollId!, targetUserIds),
        onSuccess: () => {
            toast.success('リマインドを送信しました');
        },
        onError: () => {
            toast.error('リマインドの送信に失敗しました');
        }
    });

    const handleDelete = () => {
        if (window.confirm(t('schedulePoll.confirmDelete') || 'この日程調整を削除してもよろしいですか？\n削除すると参加者の回答などもすべて消去され復元できません。')) {
            deleteMutation.mutate();
        }
    };

    // 参加者のユニークリストを作成（グリッドの列用）
    const participants = useMemo(() => {
        if (!poll) return [];
        const userMap = new Map<string, { id: string, name: string, role?: string }>();
        poll.candidates.forEach(c => {
            c.answers.forEach(a => {
                if (!userMap.has(a.user_id)) {
                    userMap.set(a.user_id, {
                        id: a.user_id,
                        name: a.display_name || a.discord_username || 'Unknown',
                        role: (a as any).role
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

            <div className="flex items-center justify-between mb-4">
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
                        {poll.required_roles && (
                            <div className="flex items-center space-x-2 mt-2">
                                <Shield className="h-4 w-4 text-indigo-500" />
                                <span className="text-xs font-bold text-gray-400">出席必須:</span>
                                <div className="flex flex-wrap gap-1">
                                    {poll.required_roles.split(',').map(role => (
                                        <span key={role} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-md text-[10px] font-bold border border-indigo-100">
                                            {role}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                <button
                    onClick={handleDelete}
                    disabled={deleteMutation.isPending}
                    className="flex items-center space-x-2 text-rose-500 hover:text-rose-600 hover:bg-rose-50 px-4 py-2 rounded-xl transition-colors disabled:opacity-50 border border-transparent hover:border-rose-100"
                >
                    <Trash2 className="h-5 w-5" />
                    <span className="font-bold text-sm hidden sm:inline">{t('common.delete') || '削除'}</span>
                </button>
            </div>

            {/* 表示モード切替 */}
            <div className="flex bg-gray-100 p-1 rounded-2xl w-fit">
                <button
                    onClick={() => setViewMode('grid')}
                    className={`flex items-center space-x-2 px-6 py-2 rounded-xl font-bold transition-all ${viewMode === 'grid' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    <LayoutGrid className="h-4 w-4" />
                    <span>{t('schedulePoll.gridView') || '表形式'}</span>
                </button>
                <button
                    onClick={() => setViewMode('calendar')}
                    className={`flex items-center space-x-2 px-6 py-2 rounded-xl font-bold transition-all ${viewMode === 'calendar' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    <Calendar className="h-4 w-4" />
                    <span>{t('schedulePoll.calendarView') || 'カレンダー'}</span>
                </button>
            </div>

            {viewMode === 'calendar' ? (
                !analysis ? (
                    <div className="flex justify-center items-center py-20 bg-white rounded-3xl border border-dashed border-gray-200">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mr-3"></div>
                        <span className="text-gray-500 font-bold">分析データを読み込み中...</span>
                    </div>
                ) : (
                    <SchedulePollCalendar
                        analysis={analysis}
                        onFinalize={(candidateId, sceneIds) => finalizeMutation.mutate({ candidateId, sceneIds })}
                    />
                )
            ) : (
                <>
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
                                                <div className="text-[10px] font-bold text-violet-500 uppercase tracking-tighter mb-0.5">{t('schedulePoll.recommendationReason') || 'おすすめ理由'}</div>
                                                <div className="text-xs text-violet-900 bg-violet-50 px-2 py-1 rounded border border-violet-100 font-medium">
                                                    {rec.reason}
                                                </div>
                                            </div>
                                        )}

                                        {rec.possible_scenes && rec.possible_scenes.length > 0 && (
                                            <div className="mb-4">
                                                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter mb-1">{t('schedulePoll.possibleScenes') || '稽古可能なシーン'}</div>
                                                <div className="space-y-1">
                                                    {rec.possible_scenes.map((ps: any) => (
                                                        <div key={ps.scene_id} className="text-[11px] text-gray-700 flex items-center bg-gray-50/50 px-1.5 py-0.5 rounded">
                                                            <span className="font-bold mr-1">#{ps.scene_number}</span>
                                                            <span className="truncate">{ps.scene_heading}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
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
                                                    {p.role && (
                                                        <span className="text-[10px] text-gray-400 mt-0.5 max-w-[100px] truncate block font-normal leading-tight">
                                                            {p.role}
                                                        </span>
                                                    )}
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

                    {/* 未回答メンバーセクション */}
                    {unansweredMembers && unansweredMembers.length > 0 && (
                        <section className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center space-x-2">
                                    <Bell className="h-5 w-5 text-amber-500" />
                                    <h2 className="text-lg font-bold text-gray-900">{t('schedulePoll.unansweredReminder') || '未回答メンバーのリマインド'}</h2>
                                </div>
                                <button
                                    onClick={() => refetchUnanswered()}
                                    className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-400 group"
                                    title={t('common.refresh') || '更新'}
                                >
                                    <RefreshCw className="h-4 w-4 group-hover:rotate-180 transition-transform duration-500" />
                                </button>
                            </div>

                            <p className="text-sm text-gray-500 mb-4">
                                {t('schedulePoll.reminderDescription') || 'まだ日程調整に回答していないメンバーです。チェックを入れたメンバーにDiscordでメンションを飛ばして通知します。'}
                            </p>

                            <div className="flex flex-wrap gap-3 mb-8">
                                {unansweredMembers.map(member => (
                                    <button
                                        key={member.user_id}
                                        onClick={() => {
                                            setTargetUserIds(prev =>
                                                prev.includes(member.user_id)
                                                    ? prev.filter(id => id !== member.user_id)
                                                    : [...prev, member.user_id]
                                            );
                                        }}
                                        className={`flex items-center space-x-3 px-4 py-2.5 rounded-2xl border transition-all duration-300 ${targetUserIds.includes(member.user_id)
                                            ? 'bg-amber-50 border-amber-200 text-amber-900 shadow-sm ring-2 ring-amber-500/10'
                                            : 'bg-gray-50 border-gray-100 text-gray-400 grayscale'
                                            }`}
                                    >
                                        <div className={`p-1.5 rounded-lg ${targetUserIds.includes(member.user_id) ? 'bg-amber-200 text-amber-700' : 'bg-gray-200 text-gray-400'}`}>
                                            {targetUserIds.includes(member.user_id) ? <UserCheck className="h-4 w-4" /> : <UserMinus className="h-4 w-4" />}
                                        </div>
                                        <div className="text-left">
                                            <div className="text-sm font-bold leading-tight">{member.name}</div>
                                            {member.role && <div className="text-[10px] uppercase font-bold tracking-wider opacity-60 leading-tight mt-0.5">{member.role}</div>}
                                        </div>
                                    </button>
                                ))}
                            </div>

                            <div className="flex justify-end">
                                <button
                                    onClick={() => remindMutation.mutate()}
                                    disabled={remindMutation.isPending || targetUserIds.length === 0}
                                    className="flex items-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white px-8 py-3 rounded-2xl font-bold shadow-lg shadow-amber-200 transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100 disabled:shadow-none"
                                >
                                    <Bell className="h-5 w-5" />
                                    <span>{t('schedulePoll.sendReminderCount', { count: targetUserIds.length }) || `${targetUserIds.length}名にリマインドを送信`}</span>
                                </button>
                            </div>
                        </section>
                    )}

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
                </>
            )}
        </div>
    );
};
