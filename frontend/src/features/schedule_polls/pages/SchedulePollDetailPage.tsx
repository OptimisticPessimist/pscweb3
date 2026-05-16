import React, { useState, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { schedulePollApi } from '../api/schedulePoll';
import { formatSceneNumber } from '@/utils/sceneFormatter';
import { projectsApi } from '@/features/projects/api/projects';
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
    RefreshCw,
    Search,
    Filter,
    ChevronRight
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { PageHead } from '@/components/PageHead';
import { useAuth } from '@/features/auth/hooks/useAuth';
import toast from 'react-hot-toast';
import { SchedulePollCalendar } from '../components/SchedulePollCalendar';

interface BatchFinalizeDraftItem {
    candidateId: string;
    title: string;
    location: string;
    notes: string;
    sceneIds: string[];
}

export const SchedulePollDetailPage: React.FC = () => {
    const { t } = useTranslation();
    const { projectId, pollId } = useParams<{ projectId: string, pollId: string }>();
    const navigate = useNavigate();
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const [selectedCandidateForFinalize, setSelectedCandidateForFinalize] = useState<string | null>(null);
    const [selectedSceneIdsForFinalize, setSelectedSceneIdsForFinalize] = useState<string[]>([]);
    const [viewMode, setViewMode] = useState<'summary' | 'grid' | 'calendar'>('summary');
    const [attendanceTarget, setAttendanceTarget] = useState<'voters_only' | 'everyone'>('voters_only');
    const [rehearsalTitle, setRehearsalTitle] = useState('');
    const [rehearsalLocation, setRehearsalLocation] = useState('未定');
    const [rehearsalNotes, setRehearsalNotes] = useState('');
    const [selectedCandidateIdsForBatch, setSelectedCandidateIdsForBatch] = useState<string[]>([]);
    const [showBatchFinalizeModal, setShowBatchFinalizeModal] = useState(false);
    const [batchAttendanceTarget, setBatchAttendanceTarget] = useState<'voters_only' | 'everyone'>('voters_only');
    const [batchDraftItems, setBatchDraftItems] = useState<BatchFinalizeDraftItem[]>([]);
    const [isEditingRequiredRoles, setIsEditingRequiredRoles] = useState(false);
    const [requiredRolesDraft, setRequiredRolesDraft] = useState<string[] | null>(null);
    const [participantSearch, setParticipantSearch] = useState('');
    const [participantRoleFilter, setParticipantRoleFilter] = useState('all');
    const [showOnlyPendingColumns, setShowOnlyPendingColumns] = useState(false);
    const gridScrollRef = useRef<HTMLDivElement | null>(null);

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

    const { data: members } = useQuery({
        queryKey: ['projectMembers', projectId],
        queryFn: () => projectsApi.getProjectMembers(projectId!),
        enabled: !!projectId
    });

    const currentMemberRole = useMemo(() => {
        if (!members || !user) return null;
        const currentMember = members.find(m => m.user_id === user.id);
        return currentMember?.role ?? null;
    }, [members, user]);

    const isViewer = currentMemberRole === 'viewer';

    const { data: analysis } = useQuery({
        queryKey: ['schedulePollAnalysis', projectId, pollId],
        queryFn: () => schedulePollApi.getCalendarAnalysis(projectId!, pollId!),
        enabled:
            !!projectId &&
            !!pollId &&
            !isViewer &&
            (viewMode === 'calendar' || !!selectedCandidateForFinalize || showBatchFinalizeModal),
    });

    const answerMutation = useMutation({
        mutationFn: ({ candidateId, status }: { candidateId: string, status: 'ok' | 'maybe' | 'ng' }) =>
            schedulePollApi.answerPoll(projectId!, pollId!, candidateId, status),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['schedulePoll', projectId, pollId] });
            toast.success(t('schedulePoll.answerSaved') || '回答を保存しました');
        },
        onError: () => {
            toast.error(t('schedulePoll.answerFailed') || '回答の保存に失敗しました。もう一度お試しください。');
        },
    });

    const [showFinalizedModal, setShowFinalizedModal] = useState(false);
    const [finalizeResultStatus, setFinalizeResultStatus] = useState<'created' | 'already_exists' | null>(null);
    const [gcalUrl, setGcalUrl] = useState<string | null>(null);

    const finalizeMutation = useMutation({
        mutationFn: ({
            candidateId,
            sceneIds,
            attendanceTarget,
            rehearsalTitle,
            rehearsalLocation,
            rehearsalNotes
        }: {
            candidateId: string;
            sceneIds: string[];
            attendanceTarget?: 'voters_only' | 'everyone';
            rehearsalTitle?: string;
            rehearsalLocation?: string;
            rehearsalNotes?: string;
        }) =>
            schedulePollApi.finalizePoll(projectId!, pollId!, {
                candidate_id: candidateId,
                scene_ids: sceneIds,
                attendance_target: attendanceTarget,
                rehearsal_title: rehearsalTitle,
                location: rehearsalLocation,
                notes: rehearsalNotes,
            }),
        onSuccess: (data) => {
            if (data.status === 'already_exists') {
                toast('同じ内容の稽古予定はすでに登録済みです');
            } else {
                toast.success(t('schedulePoll.finalized') || '稽古予定を作成しました');
            }
            setSelectedCandidateForFinalize(null);
            setSelectedSceneIdsForFinalize([]);
            setFinalizeResultStatus(data.status);
            setGcalUrl(data.gcal_url ?? null);
            setShowFinalizedModal(true);
        },
        onError: () => {
            toast.error('確定処理に失敗しました');
        },
    });

    const finalizeBatchMutation = useMutation({
        mutationFn: (items: BatchFinalizeDraftItem[]) =>
            schedulePollApi.finalizePollBatch(projectId!, pollId!, {
                items: items.map(item => ({
                    candidate_id: item.candidateId,
                    scene_ids: item.sceneIds,
                    attendance_target: batchAttendanceTarget,
                    rehearsal_title: item.title.trim() || undefined,
                    location: item.location.trim() || undefined,
                    notes: item.notes.trim() || undefined,
                }))
            }),
        onSuccess: (data) => {
            if (data.error_count === 0 && data.already_exists_count === 0) {
                toast.success(`${data.created_count}件の稽古予定を作成しました`);
            } else if (data.error_count === 0) {
                toast.success(`新規${data.created_count}件 / 既存${data.already_exists_count}件`);
            } else {
                toast.error(`新規${data.created_count}件 / 既存${data.already_exists_count}件 / 失敗${data.error_count}件`);
            }
            setShowBatchFinalizeModal(false);
            setSelectedCandidateIdsForBatch([]);
            setBatchDraftItems([]);
        },
        onError: () => {
            toast.error('一括登録に失敗しました');
        }
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

    const updateRequiredRolesMutation = useMutation({
        mutationFn: (requiredRoles: string[]) =>
            schedulePollApi.updateRequiredRoles(projectId!, pollId!, requiredRoles),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['schedulePoll', projectId, pollId] });
            queryClient.invalidateQueries({ queryKey: ['schedulePollRecommendations', projectId, pollId] });
            queryClient.invalidateQueries({ queryKey: ['schedulePollAnalysis', projectId, pollId] });
            queryClient.invalidateQueries({ queryKey: ['schedulePolls', projectId] });
            setIsEditingRequiredRoles(false);
            setRequiredRolesDraft(null);
            toast.success(t('common.saved') || '保存しました');
        },
        onError: () => {
            toast.error('必須役職の更新に失敗しました');
        },
    });

    const [excludedReminderUserIds, setExcludedReminderUserIds] = useState<string[]>([]);

    const { data: unansweredMembers, refetch: refetchUnanswered } = useQuery({
        queryKey: ['schedulePollUnanswered', projectId, pollId],
        queryFn: () => schedulePollApi.getUnansweredMembers(projectId!, pollId!),
        enabled: !!projectId && !!pollId,
    });

    const stopReminderMutation = useMutation({
        mutationFn: () => schedulePollApi.stopAutoReminder(projectId!, pollId!),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['schedulePoll', projectId, pollId] });
            toast.success(t('schedulePoll.autoReminderStopped') || '自動リマインドを停止しました');
        },
        onError: () => {
            toast.error(t('schedulePoll.stopReminderError') || '停止に失敗しました');
        }
    });

    const remindMutation = useMutation({
        mutationFn: () => schedulePollApi.remindUnansweredMembers(projectId!, pollId!, targetUserIds),
        onSuccess: () => {
            toast.success('リマインドを送信しました');
        },
        onError: () => {
            toast.error('リマインドの送信に失敗しました');
        }
    });

    const memberRoles = useMemo(() => {
        if (!members) return [];
        const roleSet = new Set<string>();
        members.forEach(member => {
            if (member.default_staff_role) {
                roleSet.add(member.default_staff_role);
            }
        });
        return Array.from(roleSet).sort();
    }, [members]);

    const currentRequiredRoles = useMemo(() => {
        if (!poll?.required_roles) return [];
        return poll.required_roles.split(',').map(role => role.trim()).filter(Boolean);
    }, [poll]);

    const requiredRolesDraftValue = requiredRolesDraft ?? currentRequiredRoles;

    const availableRequiredRoleOptions = useMemo(() => {
        const roleSet = new Set<string>([
            ...memberRoles,
            ...currentRequiredRoles,
            ...requiredRolesDraftValue,
        ]);
        return Array.from(roleSet).sort();
    }, [memberRoles, currentRequiredRoles, requiredRolesDraftValue]);

    const hasRequiredRoleChanges = useMemo(() => {
        const normalize = (roles: string[]) =>
            Array.from(new Set(roles.map(role => role.trim()).filter(Boolean))).sort();
        return normalize(currentRequiredRoles).join('|') !== normalize(requiredRolesDraftValue).join('|');
    }, [currentRequiredRoles, requiredRolesDraftValue]);

    const toggleRequiredRole = (role: string) => {
        setRequiredRolesDraft(prev => {
            const baseRoles = prev ?? currentRequiredRoles;
            return baseRoles.includes(role)
                ? baseRoles.filter(r => r !== role)
                : [...baseRoles, role];
        });
    };

    const unansweredUserIds = unansweredMembers?.map(member => member.user_id) ?? [];
    const targetUserIds = unansweredUserIds.filter(id => !excludedReminderUserIds.includes(id));

    const isEditorOrOwner = useMemo(() => {
        return currentMemberRole === 'owner' || currentMemberRole === 'editor';
    }, [currentMemberRole]);

    const isMember = useMemo(() => {
        return !!currentMemberRole;
    }, [currentMemberRole]);

    const handleDelete = () => {
        if (window.confirm(t('schedulePoll.confirmDelete') || 'この日程調整を削除してもよろしいですか？\n削除すると参加者の回答などもすべて消去され復元できません。')) {
            deleteMutation.mutate();
        }
    };

    const participants = useMemo(() => {
        if (!poll || !members) return [];
        const sourceMembers =
            isViewer && user ? members.filter(member => member.user_id === user.id) : members;

        return sourceMembers
            .map(member => {
                const answeredCount = poll.candidates.reduce((count, candidate) => {
                    return count + (candidate.answers.some(answer => answer.user_id === member.user_id) ? 1 : 0);
                }, 0);
                return {
                    id: member.user_id,
                    name: member.display_name || member.discord_username || 'Unknown',
                    role: member.default_staff_role || '',
                    answeredCount,
                    hasUnanswered: answeredCount < poll.candidates.length,
                };
            })
            .sort((a, b) => a.name.localeCompare(b.name, 'ja'));
    }, [poll, members, isViewer, user]);

    const roleFilterOptions = useMemo(() => {
        const roleSet = new Set<string>();
        participants.forEach(p => {
            if (p.role) {
                roleSet.add(p.role);
            }
        });
        return Array.from(roleSet).sort((a, b) => a.localeCompare(b, 'ja'));
    }, [participants]);

    const filteredParticipants = useMemo(() => {
        const keyword = participantSearch.trim().toLowerCase();
        return participants.filter(participant => {
            const matchKeyword =
                !keyword ||
                participant.name.toLowerCase().includes(keyword) ||
                participant.role.toLowerCase().includes(keyword);
            const matchRole = participantRoleFilter === 'all' || participant.role === participantRoleFilter;
            const matchPending = !showOnlyPendingColumns || participant.hasUnanswered;
            return matchKeyword && matchRole && matchPending;
        });
    }, [participants, participantSearch, participantRoleFilter, showOnlyPendingColumns]);

    const candidateSummaries = useMemo(() => {
        if (!poll) return [];
        return poll.candidates.map(candidate => {
            const uniqueAnswers = new Map(candidate.answers.map(answer => [answer.user_id, answer.status]));
            let okCount = 0;
            let maybeCount = 0;
            let ngCount = 0;
            uniqueAnswers.forEach(status => {
                if (status === 'ok') okCount += 1;
                if (status === 'maybe') maybeCount += 1;
                if (status === 'ng') ngCount += 1;
            });
            const totalMembers = isViewer ? 1 : (members?.length || 0);
            const unansweredCount = Math.max(0, totalMembers - uniqueAnswers.size);
            const recommendation = recommendations?.find(rec => rec.candidate_id === candidate.id);
            return {
                candidate,
                okCount,
                maybeCount,
                ngCount,
                unansweredCount,
                recommendation,
            };
        });
    }, [poll, members, recommendations, isViewer]);

    const selectedCandidateSetForBatch = useMemo(
        () => new Set(selectedCandidateIdsForBatch),
        [selectedCandidateIdsForBatch]
    );

    const toggleCandidateForBatch = (candidateId: string) => {
        setSelectedCandidateIdsForBatch(prev =>
            prev.includes(candidateId)
                ? prev.filter(id => id !== candidateId)
                : [...prev, candidateId]
        );
    };

    const selectAllCandidatesForBatch = () => {
        setSelectedCandidateIdsForBatch(candidateSummaries.map(summary => summary.candidate.id));
    };

    const clearBatchSelection = () => {
        setSelectedCandidateIdsForBatch([]);
    };

    const sceneOptionsForFinalize = useMemo(() => {
        if (analysis?.all_scenes && analysis.all_scenes.length > 0) {
            return analysis.all_scenes.map(scene => ({
                id: scene.scene_id,
                label: `#${formatSceneNumber(scene.act_number, scene.scene_number)} ${scene.heading}`
            }));
        }

        if (!selectedCandidateForFinalize || !recommendations) {
            return [];
        }

        const rec = recommendations.find(r => r.candidate_id === selectedCandidateForFinalize);
        if (!rec) {
            return [];
        }

        return rec.possible_scenes.map(scene => ({
            id: scene.scene_id,
            label: `#${formatSceneNumber(scene.act_number, scene.scene_number)} ${scene.scene_heading}`
        }));
    }, [analysis, selectedCandidateForFinalize, recommendations]);

    const openFinalizeModal = (
        candidateId: string,
        sceneIds: string[],
        target: 'voters_only' | 'everyone' = 'voters_only'
    ) => {
        const candidate = poll?.candidates.find(c => c.id === candidateId);
        const start = candidate ? new Date(candidate.start_datetime) : null;
        const defaultTitle = start
            ? `${poll?.title || '稽古'} ${start.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric' })}`
            : (poll?.title || '');

        setSelectedCandidateForFinalize(candidateId);
        setSelectedSceneIdsForFinalize(sceneIds);
        setAttendanceTarget(target);
        setRehearsalTitle(defaultTitle);
        setRehearsalLocation('未定');
        setRehearsalNotes('');
    };

    const openBatchFinalizeModal = () => {
        const drafts: BatchFinalizeDraftItem[] = selectedCandidateIdsForBatch
            .map(candidateId => {
                const summary = candidateSummaries.find(item => item.candidate.id === candidateId);
                if (!summary) return null;
                const start = new Date(summary.candidate.start_datetime);
                const defaultTitle = `${poll?.title || '稽古'} ${start.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric' })}`;
                return {
                    candidateId,
                    title: defaultTitle,
                    location: '未定',
                    notes: '',
                    sceneIds: summary.recommendation?.possible_scenes.map(scene => scene.scene_id) || [],
                };
            })
            .filter((draft): draft is BatchFinalizeDraftItem => draft !== null);

        if (drafts.length === 0) {
            toast.error('一括登録対象を選択してください');
            return;
        }

        setBatchDraftItems(drafts);
        setBatchAttendanceTarget('voters_only');
        setShowBatchFinalizeModal(true);
    };

    const updateBatchDraft = (
        candidateId: string,
        field: 'title' | 'location' | 'notes',
        value: string
    ) => {
        setBatchDraftItems(prev =>
            prev.map(item => (item.candidateId === candidateId ? { ...item, [field]: value } : item))
        );
    };

    const toggleBatchScene = (candidateId: string, sceneId: string, checked: boolean) => {
        setBatchDraftItems(prev =>
            prev.map(item => {
                if (item.candidateId !== candidateId) return item;
                return {
                    ...item,
                    sceneIds: checked
                        ? Array.from(new Set([...item.sceneIds, sceneId]))
                        : item.sceneIds.filter(id => id !== sceneId),
                };
            })
        );
    };

    const getBatchSceneOptions = (candidateId: string) => {
        if (analysis?.all_scenes && analysis.all_scenes.length > 0) {
            return analysis.all_scenes.map(scene => ({
                id: scene.scene_id,
                label: `#${formatSceneNumber(scene.act_number, scene.scene_number)} ${scene.heading}`,
            }));
        }
        const recommendation = candidateSummaries.find(summary => summary.candidate.id === candidateId)?.recommendation;
        return (
            recommendation?.possible_scenes.map(scene => ({
                id: scene.scene_id,
                label: `#${formatSceneNumber(scene.act_number, scene.scene_number)} ${scene.scene_heading}`,
            })) || []
        );
    };

    const scrollGridBy = (delta: number) => {
        if (!gridScrollRef.current) return;
        gridScrollRef.current.scrollBy({ left: delta, behavior: 'smooth' });
    };

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
                        {poll.deadline && (
                            <div className="flex items-center space-x-2 mt-2 text-rose-600">
                                <Clock className="h-4 w-4" />
                                <span className="text-xs font-bold">
                                    {t('schedulePoll.deadlineLabel') || '回答期限'}:
                                    {new Date(poll.deadline).toLocaleString(undefined, {
                                        month: 'short',
                                        day: 'numeric',
                                        weekday: 'short',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })}
                                </span>
                            </div>
                        )}
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
                {isEditorOrOwner && (
                    <button
                        onClick={handleDelete}
                        disabled={deleteMutation.isPending}
                        className="flex items-center space-x-2 text-rose-500 hover:text-rose-600 hover:bg-rose-50 px-4 py-2 rounded-xl transition-colors disabled:opacity-50 border border-transparent hover:border-rose-100"
                    >
                        <Trash2 className="h-5 w-5" />
                        <span className="font-bold text-sm hidden sm:inline">{t('common.delete') || '削除'}</span>
                    </button>
                )}
            </div>

            {/* 表示モード切替 */}
            <div className="flex bg-gray-100 p-1 rounded-2xl w-fit">
                <button
                    onClick={() => setViewMode('summary')}
                    className={`flex items-center space-x-2 px-6 py-2 rounded-xl font-bold transition-all ${viewMode === 'summary' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    <Filter className="h-4 w-4" />
                    <span>{t('schedulePoll.summaryView') || '集計'}</span>
                </button>
                <button
                    onClick={() => setViewMode('grid')}
                    className={`flex items-center space-x-2 px-6 py-2 rounded-xl font-bold transition-all ${viewMode === 'grid' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    <LayoutGrid className="h-4 w-4" />
                    <span>{t('schedulePoll.gridView') || '表形式'}</span>
                </button>
                {!isViewer && (
                    <button
                        onClick={() => setViewMode('calendar')}
                        className={`flex items-center space-x-2 px-6 py-2 rounded-xl font-bold transition-all ${viewMode === 'calendar' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Calendar className="h-4 w-4" />
                        <span>{t('schedulePoll.calendarView') || 'カレンダー'}</span>
                    </button>
                )}
            </div>

            {isEditorOrOwner && (
                <section className="bg-white shadow-xl shadow-gray-200/40 rounded-2xl border border-gray-100 p-5">
                    <div className="flex items-center justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2">
                            <Shield className="h-4 w-4 text-indigo-500" />
                            <h2 className="text-sm font-bold text-gray-800">
                                {t('schedulePoll.requiredRolesLabel') || '出席必須の役職（任意）'}
                            </h2>
                        </div>
                        {!isEditingRequiredRoles ? (
                            <button
                                onClick={() => {
                                    setRequiredRolesDraft(currentRequiredRoles);
                                    setIsEditingRequiredRoles(true);
                                }}
                                className="px-3 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg hover:bg-indigo-100 transition-colors"
                            >
                                {t('common.edit') || '編集'}
                            </button>
                        ) : (
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => {
                                        setRequiredRolesDraft(null);
                                        setIsEditingRequiredRoles(false);
                                    }}
                                    className="px-3 py-1.5 text-xs font-bold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    {t('common.cancel') || 'キャンセル'}
                                </button>
                                <button
                                    onClick={() => updateRequiredRolesMutation.mutate(requiredRolesDraftValue)}
                                    disabled={!hasRequiredRoleChanges || updateRequiredRolesMutation.isPending}
                                    className="px-3 py-1.5 text-xs font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {updateRequiredRolesMutation.isPending ? '...' : (t('common.save') || '保存')}
                                </button>
                            </div>
                        )}
                    </div>

                    {isEditingRequiredRoles ? (
                        availableRequiredRoleOptions.length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                                {availableRequiredRoleOptions.map(role => (
                                    <button
                                        key={role}
                                        type="button"
                                        onClick={() => toggleRequiredRole(role)}
                                        className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${requiredRolesDraftValue.includes(role)
                                            ? 'bg-indigo-600 text-white border-indigo-600'
                                            : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'
                                            }`}
                                    >
                                        {role}
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <p className="text-xs text-gray-500">
                                {t('schedulePoll.requiredRolesNoOptions') || '役職がないため必須役職を選択できません。'}
                            </p>
                        )
                    ) : currentRequiredRoles.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                            {currentRequiredRoles.map(role => (
                                <span key={role} className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-md text-xs font-bold border border-indigo-100">
                                    {role}
                                </span>
                            ))}
                        </div>
                    ) : (
                        <p className="text-xs text-gray-500">
                            {t('common.none') || '設定なし'}
                        </p>
                    )}
                </section>
            )}

            {viewMode === 'calendar' ? (
                !analysis ? (
                    <div className="flex justify-center items-center py-20 bg-white rounded-3xl border border-dashed border-gray-200">
                        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mr-3"></div>
                        <span className="text-gray-500 font-bold">分析データを読み込み中...</span>
                    </div>
                ) : (
                    <SchedulePollCalendar
                        analysis={analysis}
                        onFinalize={(candidateId, sceneIds, target) => openFinalizeModal(candidateId, sceneIds, target)}
                    />
                )
            ) : (
                <>
                    {/* おすすめ日程セクション */}
                    {!isViewer && recommendations && recommendations.length > 0 && (
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
                                                    {rec.possible_scenes.map((ps) => (
                                                        <div key={ps.scene_id} className="text-[11px] text-gray-700 flex items-center bg-gray-50/50 px-1.5 py-0.5 rounded">
                                                            <span className="font-bold mr-1">#{formatSceneNumber(ps.act_number, ps.scene_number)}</span>
                                                            <span className="truncate">{ps.scene_heading}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        <button
                                            onClick={() => openFinalizeModal(rec.candidate_id, rec.possible_scenes.map(scene => scene.scene_id))}
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
                    {viewMode === 'summary' ? (
                        <section className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-6">
                            <div className="flex flex-col gap-3 mb-4">
                                <div className="flex items-center justify-between">
                                    <h2 className="text-lg font-bold text-gray-900">{t('schedulePoll.summaryView') || '集計ビュー'}</h2>
                                    <span className="text-xs text-gray-500">
                                        {t('schedulePoll.summaryHint') || '候補ごとの人数集計を優先表示しています'}
                                    </span>
                                </div>
                                {isEditorOrOwner && (
                                    <div className="flex flex-wrap items-center gap-2">
                                        <button
                                            onClick={selectAllCandidatesForBatch}
                                            className="px-3 py-1.5 text-xs font-bold text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50"
                                        >
                                            すべて選択
                                        </button>
                                        <button
                                            onClick={clearBatchSelection}
                                            className="px-3 py-1.5 text-xs font-bold text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50"
                                        >
                                            選択解除
                                        </button>
                                        <button
                                            onClick={openBatchFinalizeModal}
                                            disabled={selectedCandidateIdsForBatch.length === 0}
                                            className="px-4 py-1.5 text-xs font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                                        >
                                            一括登録 ({selectedCandidateIdsForBatch.length})
                                        </button>
                                    </div>
                                )}
                            </div>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                {candidateSummaries.map(({ candidate, okCount, maybeCount, ngCount, unansweredCount, recommendation }) => {
                                    const myAnswer = candidate.answers.find(a => a.user_id === user?.id)?.status;
                                    return (
                                        <div key={candidate.id} className="border border-gray-200 rounded-xl p-4 bg-white">
                                            <div className="flex items-start justify-between gap-3">
                                                <div>
                                                    {isEditorOrOwner && (
                                                        <label className="inline-flex items-center gap-2 text-xs text-gray-600 mb-2">
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedCandidateSetForBatch.has(candidate.id)}
                                                                onChange={() => toggleCandidateForBatch(candidate.id)}
                                                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                            />
                                                            一括対象
                                                        </label>
                                                    )}
                                                    <div className="text-sm font-bold text-gray-900">
                                                        {new Date(candidate.start_datetime).toLocaleDateString(undefined, { month: 'short', day: 'numeric', weekday: 'short' })}
                                                    </div>
                                                    <div className="text-xs text-gray-500 mt-1">
                                                        {new Date(candidate.start_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                                        {' - '}
                                                        {new Date(candidate.end_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                                    </div>
                                                </div>
                                                {isEditorOrOwner && (
                                                    <button
                                                        onClick={() => openFinalizeModal(candidate.id, recommendation?.possible_scenes.map(scene => scene.scene_id) || [])}
                                                        className="text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 px-3 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors flex items-center gap-1"
                                                    >
                                                        {t('schedulePoll.finalizeThis') || 'この日で確定する'}
                                                        <ChevronRight className="h-3 w-3" />
                                                    </button>
                                                )}
                                            </div>
                                            <div className="mt-3 flex flex-wrap gap-2 text-xs font-bold">
                                                <span className="px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">OK {okCount}</span>
                                                <span className="px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-100">Maybe {maybeCount}</span>
                                                <span className="px-2 py-1 rounded bg-rose-50 text-rose-700 border border-rose-100">NG {ngCount}</span>
                                                <span className="px-2 py-1 rounded bg-gray-50 text-gray-600 border border-gray-200">{t('schedulePoll.unansweredReminder') || '未回答'} {unansweredCount}</span>
                                            </div>
                                            {recommendation?.reason && (
                                                <p className="mt-3 text-xs text-violet-800 bg-violet-50 border border-violet-100 rounded-lg px-2 py-1.5">
                                                    {recommendation.reason}
                                                </p>
                                            )}
                                            {isMember && (
                                                <div className="mt-4 flex items-center gap-2">
                                                    <button
                                                        onClick={() => answerMutation.mutate({ candidateId: candidate.id, status: 'ok' })}
                                                        className={`p-2 rounded-lg transition-all ${myAnswer === 'ok' ? 'bg-emerald-100 shadow-sm' : 'hover:bg-emerald-50'}`}
                                                    >
                                                        <CheckCircle2 className={`h-5 w-5 ${myAnswer === 'ok' ? 'text-emerald-600' : 'text-gray-300'}`} />
                                                    </button>
                                                    <button
                                                        onClick={() => answerMutation.mutate({ candidateId: candidate.id, status: 'maybe' })}
                                                        className={`p-2 rounded-lg transition-all ${myAnswer === 'maybe' ? 'bg-amber-100 shadow-sm' : 'hover:bg-amber-50'}`}
                                                    >
                                                        <HelpCircle className={`h-5 w-5 ${myAnswer === 'maybe' ? 'text-amber-600' : 'text-gray-300'}`} />
                                                    </button>
                                                    <button
                                                        onClick={() => answerMutation.mutate({ candidateId: candidate.id, status: 'ng' })}
                                                        className={`p-2 rounded-lg transition-all ${myAnswer === 'ng' ? 'bg-rose-100 shadow-sm' : 'hover:bg-rose-50'}`}
                                                    >
                                                        <XCircle className={`h-5 w-5 ${myAnswer === 'ng' ? 'text-rose-600' : 'text-gray-300'}`} />
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
                    ) : (
                        <>
                            <section className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-5">
                                <div className="flex flex-col lg:flex-row lg:items-end gap-3">
                                    <div className="flex-1">
                                        <label className="text-xs font-bold text-gray-500 mb-1 block">{t('common.search') || '検索'}</label>
                                        <div className="relative">
                                            <Search className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                            <input
                                                type="text"
                                                value={participantSearch}
                                                onChange={(e) => setParticipantSearch(e.target.value)}
                                                placeholder={t('attendance.searchPlaceholder') || '名前・役職で検索...'}
                                                className="w-full border border-gray-200 rounded-xl pl-9 pr-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                            />
                                        </div>
                                    </div>
                                    <div className="w-full lg:w-52">
                                        <label className="text-xs font-bold text-gray-500 mb-1 block">{t('schedulePoll.requiredRolesLabel') || '役職'}</label>
                                        <select
                                            value={participantRoleFilter}
                                            onChange={(e) => setParticipantRoleFilter(e.target.value)}
                                            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                        >
                                            <option value="all">{t('common.all') || 'すべて'}</option>
                                            {roleFilterOptions.map(role => (
                                                <option key={role} value={role}>{role}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <label className="inline-flex items-center gap-2 text-sm text-gray-700 px-3 py-2.5 border border-gray-200 rounded-xl bg-gray-50">
                                        <input
                                            type="checkbox"
                                            checked={showOnlyPendingColumns}
                                            onChange={(e) => setShowOnlyPendingColumns(e.target.checked)}
                                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                        />
                                        <span>{t('schedulePoll.unansweredReminder') || '未回答'}のみ</span>
                                    </label>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => scrollGridBy(-420)}
                                            className="px-3 py-2.5 border border-gray-200 rounded-xl text-sm font-bold text-gray-700 hover:bg-gray-50"
                                        >
                                            ←
                                        </button>
                                        <button
                                            onClick={() => scrollGridBy(420)}
                                            className="px-3 py-2.5 border border-gray-200 rounded-xl text-sm font-bold text-gray-700 hover:bg-gray-50"
                                        >
                                            →
                                        </button>
                                    </div>
                                </div>
                                <p className="text-xs text-gray-500 mt-3">
                                    {filteredParticipants.length}/{participants.length} {t('schedulePoll.summaryView') || '表示'}
                                </p>
                            </section>

                            <div className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 overflow-hidden">
                                <div ref={gridScrollRef} className="overflow-x-auto">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-gray-50/50 border-b border-gray-100">
                                                <th className="px-6 py-5 text-sm font-bold text-gray-700 w-64 sticky left-0 bg-white z-10 backdrop-blur-sm shadow-[1px_0_0_0_rgba(0,0,0,0.05)]">
                                                    {t('schedulePoll.dateColumn') || '候補日時'}
                                                </th>
                                                {filteredParticipants.map(p => (
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
                                                {isMember && (
                                                    <th className="px-6 py-5 text-sm font-bold text-gray-700 text-center min-w-[150px]">
                                                        {t('schedulePoll.myAnswer') || 'あなたの回答'}
                                                    </th>
                                                )}
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
                                                        {filteredParticipants.map(p => {
                                                            const status = candidate.answers.find(a => a.user_id === p.id)?.status;
                                                            return (
                                                                <td key={p.id} className="px-6 py-5 text-center">
                                                                    <div className="flex justify-center">
                                                                        {getStatusIcon(status)}
                                                                    </div>
                                                                </td>
                                                            );
                                                        })}
                                                        {isMember && (
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
                                                        )}
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    )}

                    {/* 未回答メンバーセクション */}
                    {unansweredMembers && unansweredMembers.length > 0 && (
                        <section className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center space-x-2">
                                    <Bell className="h-5 w-5 text-amber-500" />
                                    <h2 className="text-lg font-bold text-gray-900">
                                        {t('schedulePoll.unansweredReminder') || '未回答メンバーのリマインド'} ({unansweredMembers.length}名)
                                    </h2>
                                </div>
                                <div className="flex items-center space-x-2">
                                    {isEditorOrOwner && !poll.auto_reminder_stopped && poll.deadline && (
                                        <button
                                            onClick={() => {
                                                if (window.confirm(t('schedulePoll.confirmStopReminder') || '以前に設定された回答期限による自動リマインド送信を停止しますか？')) {
                                                    stopReminderMutation.mutate();
                                                }
                                            }}
                                            disabled={stopReminderMutation.isPending}
                                            className="text-xs font-bold text-rose-600 hover:text-rose-700 bg-rose-50 px-3 py-2 rounded-lg transition-colors flex items-center"
                                        >
                                            <Bell className="h-3 w-3 mr-1" />
                                            {stopReminderMutation.isPending ? '...' : (t('schedulePoll.stopAutoReminder') || '自動リマインド停止')}
                                        </button>
                                    )}
                                    {poll.auto_reminder_stopped && (
                                        <span className="text-xs font-bold text-gray-400 bg-gray-50 px-3 py-2 rounded-lg flex items-center border border-gray-100 italic">
                                            {t('schedulePoll.autoReminderIsStopped') || '自動リマインド停止済み'}
                                        </span>
                                    )}
                                    <button
                                        onClick={() => refetchUnanswered()}
                                        className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-400 group"
                                        title={t('common.refresh') || '更新'}
                                    >
                                        <RefreshCw className="h-4 w-4 group-hover:rotate-180 transition-transform duration-500" />
                                    </button>
                                </div>
                            </div>

                            <p className="text-sm text-gray-500 mb-4">
                                {t('schedulePoll.reminderDescription') || 'まだ日程調整に回答していないメンバーです。チェックを入れたメンバーにDiscordでメンションを飛ばして通知します。'}
                            </p>

                            <div className="flex flex-wrap gap-3 mb-8">
                                {unansweredMembers.map(member => (
                                    <button
                                        key={member.user_id}
                                        onClick={() => {
                                            setExcludedReminderUserIds(prev =>
                                                targetUserIds.includes(member.user_id)
                                                    ? [...prev, member.user_id]
                                                    : prev.filter(id => id !== member.user_id)
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

                    {/* 確定用モーダル（詳細入力ステップ付き） */}
                    {selectedCandidateForFinalize && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm overflow-y-auto">
                            <div className="bg-white rounded-3xl p-8 max-w-xl w-full shadow-2xl animate-in zoom-in duration-300">
                                <div className="flex flex-col space-y-6">
                                    <div className="flex items-center space-x-3 mb-2">
                                        <div className="p-3 bg-violet-100 rounded-2xl">
                                            <Sparkles className="h-6 w-6 text-violet-600" />
                                        </div>
                                        <h2 className="text-xl font-bold text-gray-900">{t('schedulePoll.finalizeTitle') || '予定を確定する'}</h2>
                                    </div>

                                    <div className="p-4 bg-gray-50 rounded-2xl">
                                        <div className="text-sm font-bold text-gray-900">
                                            {new Date(poll.candidates.find(c => c.id === selectedCandidateForFinalize)?.start_datetime || '').toLocaleDateString(undefined, { month: 'long', day: 'numeric', weekday: 'long' })}
                                        </div>
                                        <div className="text-sm text-gray-600 mt-1">
                                            {new Date(poll.candidates.find(c => c.id === selectedCandidateForFinalize)?.start_datetime || '').toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                            {' - '}
                                            {new Date(poll.candidates.find(c => c.id === selectedCandidateForFinalize)?.end_datetime || '').toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-gray-700">
                                            {t('schedulePoll.titleLabel') || 'タイトル'}
                                        </label>
                                        <input
                                            type="text"
                                            value={rehearsalTitle}
                                            onChange={(e) => setRehearsalTitle(e.target.value)}
                                            placeholder="例: 5月後半 抜き稽古"
                                            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-gray-700">
                                            {t('schedule.location') || '場所'}
                                        </label>
                                        <input
                                            type="text"
                                            value={rehearsalLocation}
                                            onChange={(e) => setRehearsalLocation(e.target.value)}
                                            placeholder="例: 第2稽古場"
                                            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-gray-700">
                                            {t('schedule.notes') || 'メモ'}
                                        </label>
                                        <textarea
                                            rows={3}
                                            value={rehearsalNotes}
                                            onChange={(e) => setRehearsalNotes(e.target.value)}
                                            placeholder="連絡事項や当日のメモ"
                                            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none resize-y"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-gray-700">
                                            {t('schedulePoll.possibleScenes') || '稽古シーン'}
                                        </label>
                                        <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-xl p-3 space-y-2">
                                            {sceneOptionsForFinalize.length === 0 ? (
                                                <p className="text-xs text-gray-500">
                                                    {t('schedulePoll.noPossibleScenes') || '選択可能なシーンがありません。'}
                                                </p>
                                            ) : (
                                                sceneOptionsForFinalize.map(scene => (
                                                    <label key={scene.id} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            checked={selectedSceneIdsForFinalize.includes(scene.id)}
                                                            onChange={(e) => {
                                                                if (e.target.checked) {
                                                                    setSelectedSceneIdsForFinalize(prev => [...prev, scene.id]);
                                                                } else {
                                                                    setSelectedSceneIdsForFinalize(prev => prev.filter(id => id !== scene.id));
                                                                }
                                                            }}
                                                            className="rounded border-gray-300 text-violet-600 focus:ring-violet-500"
                                                        />
                                                        <span>{scene.label}</span>
                                                    </label>
                                                ))
                                            )}
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <label className="text-sm font-bold text-gray-700">{t('schedulePoll.attendanceTargetLabel') || '出欠確認の対象者'}</label>
                                        <div className="grid grid-cols-2 gap-3">
                                            <label className={`flex flex-col p-4 border rounded-xl cursor-pointer transition-all ${attendanceTarget === 'voters_only' ? 'border-violet-500 bg-violet-50/50 shadow-sm ring-1 ring-violet-500' : 'border-gray-200 hover:bg-gray-50'}`}>
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <input
                                                        type="radio"
                                                        name="attendance_target"
                                                        value="voters_only"
                                                        checked={attendanceTarget === 'voters_only'}
                                                        onChange={() => setAttendanceTarget('voters_only')}
                                                        className="text-violet-600 focus:ring-violet-500"
                                                    />
                                                    <span className="text-sm font-bold text-gray-900">{t('schedulePoll.targetVotersOnly') || '回答者のみ'}</span>
                                                </div>
                                                <span className="text-xs text-gray-500 ml-6">{t('schedulePoll.targetVotersOnlyDesc') || 'OKまたはMaybeと回答したメンバー'}</span>
                                            </label>
                                            <label className={`flex flex-col p-4 border rounded-xl cursor-pointer transition-all ${attendanceTarget === 'everyone' ? 'border-violet-500 bg-violet-50/50 shadow-sm ring-1 ring-violet-500' : 'border-gray-200 hover:bg-gray-50'}`}>
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <input
                                                        type="radio"
                                                        name="attendance_target"
                                                        value="everyone"
                                                        checked={attendanceTarget === 'everyone'}
                                                        onChange={() => setAttendanceTarget('everyone')}
                                                        className="text-violet-600 focus:ring-violet-500"
                                                    />
                                                    <span className="text-sm font-bold text-gray-900">{t('schedulePoll.targetEveryone') || '全員'}</span>
                                                </div>
                                                <span className="text-xs text-gray-500 ml-6">{t('schedulePoll.targetEveryoneDesc') || 'プロジェクトメンバー全員'}</span>
                                            </label>
                                        </div>
                                    </div>

                                    <p className="text-sm text-gray-500 leading-relaxed">
                                        {t('schedulePoll.finalizeConfirm') || 'この内容で稽古予定を作成します。'}
                                    </p>

                                    <div className="flex space-x-3 pt-2">
                                        <button
                                            onClick={() => {
                                                setSelectedCandidateForFinalize(null);
                                                setSelectedSceneIdsForFinalize([]);
                                            }}
                                            className="flex-1 py-3 border border-gray-200 text-gray-700 font-bold rounded-xl hover:bg-gray-50 transition-colors"
                                        >
                                            {t('common.cancel')}
                                        </button>
                                        <button
                                            onClick={() => {
                                                finalizeMutation.mutate({
                                                    candidateId: selectedCandidateForFinalize,
                                                    sceneIds: selectedSceneIdsForFinalize,
                                                    attendanceTarget: attendanceTarget,
                                                    rehearsalTitle: rehearsalTitle.trim() || undefined,
                                                    rehearsalLocation: rehearsalLocation.trim() || undefined,
                                                    rehearsalNotes: rehearsalNotes.trim() || undefined,
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
                        </div>
                    )}

                    {showBatchFinalizeModal && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm overflow-y-auto">
                            <div className="bg-white rounded-3xl p-6 max-w-4xl w-full shadow-2xl animate-in zoom-in duration-300">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-xl font-bold text-gray-900">一括登録の詳細設定</h2>
                                    <button
                                        onClick={() => setShowBatchFinalizeModal(false)}
                                        className="px-3 py-1.5 text-xs font-bold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
                                    >
                                        閉じる
                                    </button>
                                </div>

                                <div className="mb-4 p-3 border border-indigo-100 bg-indigo-50 rounded-xl">
                                    <label className="text-sm font-bold text-gray-700 block mb-2">{t('schedulePoll.attendanceTargetLabel') || '出欠確認の対象者'}</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        <label className={`flex items-center gap-2 p-2 rounded-lg border ${batchAttendanceTarget === 'voters_only' ? 'border-indigo-400 bg-white' : 'border-gray-200 bg-white'}`}>
                                            <input
                                                type="radio"
                                                name="batch_attendance_target"
                                                checked={batchAttendanceTarget === 'voters_only'}
                                                onChange={() => setBatchAttendanceTarget('voters_only')}
                                                className="text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="text-sm">{t('schedulePoll.targetVotersOnly') || '回答者のみ'}</span>
                                        </label>
                                        <label className={`flex items-center gap-2 p-2 rounded-lg border ${batchAttendanceTarget === 'everyone' ? 'border-indigo-400 bg-white' : 'border-gray-200 bg-white'}`}>
                                            <input
                                                type="radio"
                                                name="batch_attendance_target"
                                                checked={batchAttendanceTarget === 'everyone'}
                                                onChange={() => setBatchAttendanceTarget('everyone')}
                                                className="text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="text-sm">{t('schedulePoll.targetEveryone') || '全員'}</span>
                                        </label>
                                    </div>
                                </div>

                                <div className="max-h-[55vh] overflow-y-auto space-y-4 pr-1">
                                    {batchDraftItems.map(item => {
                                        const candidate = poll.candidates.find(c => c.id === item.candidateId);
                                        const sceneOptions = getBatchSceneOptions(item.candidateId);
                                        return (
                                            <div key={item.candidateId} className="border border-gray-200 rounded-xl p-4">
                                                <div className="text-sm font-bold text-gray-900 mb-2">
                                                    {candidate
                                                        ? `${new Date(candidate.start_datetime).toLocaleDateString(undefined, { month: 'short', day: 'numeric', weekday: 'short' })} ${new Date(candidate.start_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}`
                                                        : item.candidateId}
                                                </div>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                    <div>
                                                        <label className="text-xs font-bold text-gray-600">タイトル</label>
                                                        <input
                                                            type="text"
                                                            value={item.title}
                                                            onChange={(e) => updateBatchDraft(item.candidateId, 'title', e.target.value)}
                                                            className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="text-xs font-bold text-gray-600">{t('schedule.location') || '場所'}</label>
                                                        <input
                                                            type="text"
                                                            value={item.location}
                                                            onChange={(e) => updateBatchDraft(item.candidateId, 'location', e.target.value)}
                                                            className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                                        />
                                                    </div>
                                                </div>
                                                <div className="mt-3">
                                                    <label className="text-xs font-bold text-gray-600">{t('schedule.notes') || 'メモ'}</label>
                                                    <textarea
                                                        rows={2}
                                                        value={item.notes}
                                                        onChange={(e) => updateBatchDraft(item.candidateId, 'notes', e.target.value)}
                                                        className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-y"
                                                    />
                                                </div>
                                                <div className="mt-3">
                                                    <label className="text-xs font-bold text-gray-600">{t('schedulePoll.possibleScenes') || '稽古シーン'}</label>
                                                    <div className="mt-1 max-h-28 overflow-y-auto border border-gray-200 rounded-lg p-2 space-y-1">
                                                        {sceneOptions.length === 0 ? (
                                                            <div className="text-xs text-gray-500">{t('schedulePoll.noPossibleScenes') || '選択可能なシーンがありません。'}</div>
                                                        ) : (
                                                            sceneOptions.map(scene => (
                                                                <label key={scene.id} className="flex items-center gap-2 text-xs text-gray-700">
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={item.sceneIds.includes(scene.id)}
                                                                        onChange={(e) => toggleBatchScene(item.candidateId, scene.id, e.target.checked)}
                                                                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                                    />
                                                                    <span>{scene.label}</span>
                                                                </label>
                                                            ))
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className="mt-5 flex justify-end gap-3">
                                    <button
                                        onClick={() => setShowBatchFinalizeModal(false)}
                                        className="px-4 py-2 border border-gray-200 text-gray-700 font-bold rounded-lg hover:bg-gray-50"
                                    >
                                        {t('common.cancel') || 'キャンセル'}
                                    </button>
                                    <button
                                        onClick={() => finalizeBatchMutation.mutate(batchDraftItems)}
                                        disabled={finalizeBatchMutation.isPending || batchDraftItems.length === 0}
                                        className="px-5 py-2 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                                    >
                                        {finalizeBatchMutation.isPending ? '...' : `一括登録する (${batchDraftItems.length})`}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                </>
            )}

            {showFinalizedModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-6 text-center">
                        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                            <CheckCircle2 className="h-6 w-6 text-green-600" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                            {finalizeResultStatus === 'already_exists'
                                ? '同じ予定がすでに登録されています'
                                : t('schedulePoll.finalizedModalTitle')}
                        </h3>
                        <p className="text-sm text-gray-500 mb-6">
                            {finalizeResultStatus === 'already_exists'
                                ? '重複登録は行われませんでした。既存の稽古予定を利用してください。'
                                : t('schedulePoll.finalizedModalDescription')}
                        </p>
                        <div className="space-y-3">
                            {gcalUrl && (
                                <a
                                    href={gcalUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                                >
                                    <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V8h14v12z" />
                                    </svg>
                                    {t('schedulePoll.addToGoogleCalendar')}
                                </a>
                            )}
                            <button
                                onClick={() => navigate(`/projects/${projectId}/schedule`)}
                                className="w-full py-3 px-4 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                            >
                                {t('schedulePoll.goToSchedule')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
