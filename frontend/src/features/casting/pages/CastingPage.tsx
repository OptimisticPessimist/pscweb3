import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { charactersApi } from '../api/characters';
import { projectsApi } from '@/features/projects/api/projects';
import type { ApiError } from '@/types';
import { useTranslation } from 'react-i18next';


export const CastingPage = () => {
    const { t } = useTranslation();
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();

    // UI State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedCharId, setSelectedCharId] = useState<string | null>(null);
    const [selectedUserId, setSelectedUserId] = useState<string>('');
    const [castName, setCastName] = useState<string>('');

    // Queries
    const { data: project } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    const { data: characters, isLoading: charsLoading } = useQuery({
        queryKey: ['characters', projectId],
        queryFn: () => charactersApi.getCharacters(projectId!),
        enabled: !!projectId,
    });

    const { data: members } = useQuery({
        queryKey: ['members', projectId],
        queryFn: () => projectsApi.getProjectMembers(projectId!),
        enabled: !!projectId,
    });

    // Mutations
    const addCastingMutation = useMutation({
        mutationFn: (data: { charId: string, userId: string, castName?: string }) =>
            charactersApi.addCasting(projectId!, data.charId, data.userId, data.castName),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['characters', projectId] });
            closeModal();
        },
        onError: (error: ApiError) => {
            alert('Failed to add casting: ' + (error.response?.data?.detail || error.message));
        }
    });

    const removeCastingMutation = useMutation({
        mutationFn: (data: { charId: string, userId: string }) =>
            charactersApi.removeCasting(projectId!, data.charId, data.userId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['characters', projectId] });
        },
        onError: (error: ApiError) => {
            alert('Failed to remove casting: ' + (error.response?.data?.detail || error.message));
        }
    });

    // ... (inside JSX)
    const openModal = (charId: string) => {
        setSelectedCharId(charId);
        setSelectedUserId('');
        setCastName('');
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setSelectedCharId(null);
    };

    const handleAdd = () => {
        if (selectedCharId && selectedUserId) {
            addCastingMutation.mutate({
                charId: selectedCharId,
                userId: selectedUserId,
                castName: castName || undefined
            });
        }
    };

    const handleRemove = (charId: string, userId: string) => {
        // 確認ダイアログが原因で削除できないケースがあるため、一時的にダイアログを廃止します。
        // 将来的にはカスタムモーダル等の実装を検討します。
        removeCastingMutation.mutate({ charId, userId });
    };

    const isEditable = project?.role === 'owner' || project?.role === 'editor';

    if (charsLoading) return <div className="p-8 text-center">{t('casting.loadingCharacters')}</div>;
    if (!characters || characters.length === 0) return (
        <div className="p-8 text-center text-gray-500">
            {t('script.noScript')}
        </div>
    );

    return (
        <div className="space-y-6">
            <div className="md:flex md:items-center md:justify-between">
                <div className="min-w-0 flex-1">
                    <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                        {t('casting.title')}
                    </h2>
                </div>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/3">
                                {t('casting.character')}
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                {t('casting.actor')}
                            </th>
                            {isEditable && (
                                <th scope="col" className="relative px-6 py-3">
                                    <span className="sr-only">Edit</span>
                                </th>
                            )}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {characters.map((char) => (
                            <tr key={char.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {char.name}
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-500">
                                    <div className="flex flex-wrap gap-2">
                                        {char.castings.map((cast) => (
                                            <span key={cast.user_id} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                                                {cast.display_name || cast.discord_username}
                                                {cast.cast_name && <span className="ml-1 text-indigo-600">({cast.cast_name})</span>}
                                                {isEditable && (
                                                    <button
                                                        type="button"
                                                        onClick={(e) => {
                                                            e.preventDefault();
                                                            e.stopPropagation();
                                                            handleRemove(char.id, cast.user_id);
                                                        }}
                                                        className="flex-shrink-0 ml-1.5 h-4 w-4 rounded-full inline-flex items-center justify-center text-indigo-400 hover:bg-indigo-200 hover:text-indigo-500 focus:outline-none focus:bg-indigo-500 focus:text-white"
                                                    >
                                                        <span className="sr-only">Remove cast</span>
                                                        <svg className="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8">
                                                            <path strokeLinecap="round" strokeWidth="1.5" d="M1 1l6 6m0-6L1 7" />
                                                        </svg>
                                                    </button>
                                                )}
                                            </span>
                                        ))}
                                        {char.castings.length === 0 && <span className="text-gray-400 italic">{t('casting.unassigned')}</span>}
                                    </div>
                                </td>
                                {isEditable && (
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => openModal(char.id)}
                                            className="text-indigo-600 hover:text-indigo-900"
                                        >
                                            {t('casting.assign')}
                                        </button>
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Simple Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                    <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
                        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={closeModal}></div>

                        <div className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                            <div>
                                <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                                    Assign Cast
                                </h3>
                                <div className="mt-4 space-y-4">
                                    <div>
                                        <label htmlFor="member" className="block text-sm font-medium text-gray-700">{t('casting.member')}</label>
                                        <select
                                            id="member"
                                            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-white text-gray-900"
                                            value={selectedUserId}
                                            onChange={(e) => setSelectedUserId(e.target.value)}
                                        >
                                            <option value="">Select a member</option>
                                            {members?.map((member) => (
                                                <option key={member.user_id} value={member.user_id}>
                                                    {member.display_name || member.discord_username}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label htmlFor="castName" className="block text-sm font-medium text-gray-700">{t('casting.memo')} ({t('casting.optional')})</label>
                                        <input
                                            type="text"
                                            id="castName"
                                            className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border border-gray-300 rounded-md p-2 bg-white text-gray-900"
                                            placeholder="e.g. Pattern A"
                                            value={castName}
                                            onChange={(e) => setCastName(e.target.value)}
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                                <button
                                    type="button"
                                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
                                    onClick={handleAdd}
                                    disabled={!selectedUserId || addCastingMutation.isPending}
                                >
                                    {addCastingMutation.isPending ? t('common.loading') : t('common.save')}
                                </button>
                                <button
                                    type="button"
                                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                                    onClick={closeModal}
                                >
                                    {t('common.cancel')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
