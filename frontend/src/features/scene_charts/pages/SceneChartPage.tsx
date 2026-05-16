import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scriptsApi } from '@/features/scripts/api/scripts';
import { sceneChartsApi } from '@/features/scene_charts/api/sceneCharts';
import { charactersApi } from '@/features/casting/api/characters';
import { projectsApi } from '@/features/projects/api/projects';
import { useTranslation } from 'react-i18next';
import { formatSceneNumber } from '@/utils/sceneFormatter';
import type { CharacterInScene } from '@/types';

export const SceneChartPage = () => {
    const { t, i18n } = useTranslation();
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();
    const [selectedScriptId, setSelectedScriptId] = useState<string>('');

    // モーダル状態
    const [showAddCharModal, setShowAddCharModal] = useState(false);
    const [showAddSceneModal, setShowAddSceneModal] = useState(false);
    const [showEditSceneModal, setShowEditSceneModal] = useState<{
        sceneId: string; heading: string; actNumber: number | null; sceneNumber: number; isCustom: boolean;
    } | null>(null);
    const [newCharName, setNewCharName] = useState('');
    const [newSceneData, setNewSceneData] = useState({ heading: '', actNumber: '', sceneNumber: '' });
    const [editSceneData, setEditSceneData] = useState({ heading: '', actNumber: '', sceneNumber: '' });

    // プロジェクト情報（権限チェック用）
    const { data: project } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    const isEditable = project?.role === 'owner' || project?.role === 'editor';

    // 脚本一覧
    const { data: scripts, isLoading: scriptsLoading } = useQuery({
        queryKey: ['scripts', projectId],
        queryFn: () => scriptsApi.getScripts(projectId!),
        enabled: !!projectId,
    });

    useEffect(() => {
        if (scripts && scripts.length > 0 && !selectedScriptId) {
            const sortedScripts = [...scripts].sort((a, b) =>
                new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
            );
            setSelectedScriptId(sortedScripts[0].id);
        } else if (scripts && scripts.length > 0 && selectedScriptId) {
            const exists = scripts.find(s => s.id === selectedScriptId);
            if (!exists) {
                setSelectedScriptId(scripts[0].id);
            }
        }
    }, [scripts, selectedScriptId]);

    // 香盤表
    const { data: chart, isLoading: chartLoading } = useQuery({
        queryKey: ['sceneChart', selectedScriptId],
        queryFn: () => sceneChartsApi.getSceneChart(selectedScriptId),
        enabled: !!selectedScriptId,
        retry: false,
    });

    // Mutations
    const addMappingMutation = useMutation({
        mutationFn: ({ sceneId, characterId }: { sceneId: string; characterId: string }) =>
            sceneChartsApi.addMapping(projectId!, sceneId, characterId),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sceneChart', selectedScriptId] }),
    });

    const removeMappingMutation = useMutation({
        mutationFn: ({ sceneId, characterId }: { sceneId: string; characterId: string }) =>
            sceneChartsApi.removeMapping(projectId!, sceneId, characterId),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sceneChart', selectedScriptId] }),
    });

    const addCharMutation = useMutation({
        mutationFn: (name: string) => charactersApi.createCustomCharacter(projectId!, name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sceneChart', selectedScriptId] });
            queryClient.invalidateQueries({ queryKey: ['characters', projectId] });
            setShowAddCharModal(false);
            setNewCharName('');
        },
    });

    const deleteCharMutation = useMutation({
        mutationFn: (characterId: string) => charactersApi.deleteCustomCharacter(projectId!, characterId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sceneChart', selectedScriptId] });
            queryClient.invalidateQueries({ queryKey: ['characters', projectId] });
        },
    });

    const addSceneMutation = useMutation({
        mutationFn: (data: { heading: string; act_number?: number | null; scene_number: number }) =>
            sceneChartsApi.createScene(projectId!, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sceneChart', selectedScriptId] });
            setShowAddSceneModal(false);
            setNewSceneData({ heading: '', actNumber: '', sceneNumber: '' });
        },
    });

    const deleteSceneMutation = useMutation({
        mutationFn: (sceneId: string) => sceneChartsApi.deleteScene(projectId!, sceneId),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sceneChart', selectedScriptId] }),
    });

    const updateSceneMutation = useMutation({
        mutationFn: ({ sceneId, data }: { sceneId: string; data: { heading?: string; act_number?: number | null; scene_number?: number } }) =>
            sceneChartsApi.updateScene(projectId!, sceneId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sceneChart', selectedScriptId] });
            setShowEditSceneModal(null);
        },
    });

    // キャラクター一覧（全シーンのunion + 脚本全キャラ）
    const { data: allCharacters } = useQuery({
        queryKey: ['characters', projectId],
        queryFn: () => charactersApi.getCharacters(projectId!),
        enabled: !!projectId,
    });

    const handleCellClick = (sceneId: string, char: { id: string; isAppearing: boolean; isManual: boolean }) => {
        if (!isEditable) return;

        if (!char.isAppearing) {
            // 未出演 → 手動追加
            addMappingMutation.mutate({ sceneId, characterId: char.id });
        } else if (char.isManual) {
            // 手動マッピング → 削除
            removeMappingMutation.mutate({ sceneId, characterId: char.id });
        }
        // 自動マッピング（●）はクリック不可
    };

    if (scriptsLoading) return <div className="p-8 text-center">{t('common.loading')}</div>;
    if (!scripts || scripts.length === 0) return (
        <div className="p-8 text-center text-gray-500">
            {t('script.noScript')}
        </div>
    );

    // 全キャラクターマップ（chartのデータ + allCharactersから）
    const uniqueChars = new Map<string, { id: string; name: string; order: number; is_custom: boolean }>();
    if (chart) {
        chart.scenes.forEach(scene => {
            scene.characters.forEach(char => {
                if (!uniqueChars.has(char.id)) {
                    uniqueChars.set(char.id, { id: char.id, name: char.name, order: char.order, is_custom: char.is_custom });
                }
            });
        });
    }
    // allCharactersからも追加（マッピングがないキャラクターも表示）
    if (allCharacters) {
        allCharacters.forEach(char => {
            if (!uniqueChars.has(char.id)) {
                uniqueChars.set(char.id, { id: char.id, name: char.name, order: 9999, is_custom: char.is_custom });
            }
        });
    }
    const sortedChars = Array.from(uniqueChars.values()).sort((a, b) => a.order - b.order);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6 flex flex-col sm:flex-row justify-between items-center gap-4">
                <div className="w-full sm:w-auto">
                    <h3 className="text-lg font-medium leading-6 text-gray-900">{t('sceneChart.title')}</h3>
                    {scripts && scripts[0] && scripts[0].title && (
                        <p className="mt-1 text-sm text-gray-500">
                            {t('script.title')}: {scripts[0].title} (Rev.{scripts[0].revision}) - {new Date(scripts[0].uploaded_at).toLocaleString(i18n.language, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </p>
                    )}
                </div>
                {isEditable && (
                    <div className="flex gap-2">
                        <button
                            onClick={() => setShowAddCharModal(true)}
                            className="inline-flex items-center px-3 py-1.5 border border-amber-300 text-sm font-medium rounded-md text-amber-700 bg-amber-50 hover:bg-amber-100"
                        >
                            + {t('sceneChart.addCharacter')}
                        </button>
                        <button
                            onClick={() => setShowAddSceneModal(true)}
                            className="inline-flex items-center px-3 py-1.5 border border-amber-300 text-sm font-medium rounded-md text-amber-700 bg-amber-50 hover:bg-amber-100"
                        >
                            + {t('sceneChart.addScene')}
                        </button>
                    </div>
                )}
            </div>

            {/* Matrix View */}
            {chartLoading ? (
                <div className="p-12 text-center text-gray-500">{t('sceneChart.loadingChart')}</div>
            ) : chart && (chart.scenes.length > 0 || sortedChars.length > 0) ? (
                <>
                    <div className="bg-white shadow overflow-hidden sm:rounded-lg overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10 w-16 border-r border-gray-200">
                                        Act
                                    </th>
                                    <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-16 bg-gray-50 z-10 w-20 border-r border-gray-200">
                                        Scene
                                    </th>
                                    <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-36 bg-gray-50 z-10 border-r border-gray-200 min-w-[200px]">
                                        Heading
                                    </th>
                                    {sortedChars.map(char => (
                                        <th key={char.id} scope="col" className={`px-2 py-3 text-center text-xs font-medium uppercase tracking-wider w-12 ${char.is_custom ? 'text-amber-700 bg-amber-50' : 'text-gray-500'}`}>
                                            <div style={{ writingMode: 'vertical-rl', textOrientation: 'upright' }} className={`mx-auto whitespace-nowrap h-32 flex items-center justify-center ${char.is_custom ? 'italic' : ''}`}>
                                                {char.name}
                                            </div>
                                            {isEditable && char.is_custom && (
                                                <button
                                                    onClick={() => {
                                                        if (confirm(t('sceneChart.deleteConfirm'))) {
                                                            deleteCharMutation.mutate(char.id);
                                                        }
                                                    }}
                                                    className="text-red-400 hover:text-red-600 text-xs mt-1"
                                                    title="Delete"
                                                >
                                                    x
                                                </button>
                                            )}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {chart.scenes.map((scene) => {
                                    const sceneCharMap = new Map<string, CharacterInScene>();
                                    scene.characters.forEach(c => sceneCharMap.set(c.id, c));

                                    return (
                                        <tr key={scene.scene_id} className={`hover:bg-gray-50 ${scene.is_custom ? 'bg-amber-50/30' : ''}`}>
                                            <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 sticky left-0 bg-white group-hover:bg-gray-50 font-bold border-r border-gray-100">
                                                {scene.act_number ? `#${scene.act_number}` : '-'}
                                            </td>
                                            <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 sticky left-16 bg-white group-hover:bg-gray-50 font-bold border-r border-gray-100">
                                                #{formatSceneNumber(scene.act_number, scene.scene_number)}
                                            </td>
                                            <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500 sticky left-36 bg-white group-hover:bg-gray-50 border-r border-gray-200 max-w-xs truncate" title={scene.scene_heading}>
                                                <span className="flex items-center gap-1">
                                                    {scene.scene_heading}
                                                    {isEditable && (
                                                        <button
                                                            onClick={() => {
                                                                setShowEditSceneModal({
                                                                    sceneId: scene.scene_id,
                                                                    heading: scene.scene_heading,
                                                                    actNumber: scene.act_number ?? null,
                                                                    sceneNumber: scene.scene_number,
                                                                    isCustom: scene.is_custom,
                                                                });
                                                                setEditSceneData({
                                                                    heading: scene.scene_heading,
                                                                    actNumber: scene.act_number?.toString() ?? '',
                                                                    sceneNumber: scene.scene_number.toString(),
                                                                });
                                                            }}
                                                            className="text-gray-400 hover:text-gray-600 ml-1 flex-shrink-0"
                                                            title={t('sceneChart.editScene')}
                                                        >
                                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                                            </svg>
                                                        </button>
                                                    )}
                                                    {isEditable && scene.is_custom && (
                                                        <button
                                                            onClick={() => {
                                                                if (confirm(t('sceneChart.deleteConfirm'))) {
                                                                    deleteSceneMutation.mutate(scene.scene_id);
                                                                }
                                                            }}
                                                            className="text-red-400 hover:text-red-600 ml-1 flex-shrink-0"
                                                            title="Delete"
                                                        >
                                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                            </svg>
                                                        </button>
                                                    )}
                                                </span>
                                            </td>
                                            {sortedChars.map(char => {
                                                const mapping = sceneCharMap.get(char.id);
                                                const isAppearing = !!mapping;
                                                const isManual = mapping?.is_manual ?? false;

                                                let symbol: string;
                                                let cellClass: string;
                                                let cursorClass = '';
                                                let titleText = '';

                                                if (isAppearing && !isManual) {
                                                    // 自動（セリフあり）
                                                    symbol = '\u25CF'; // ●
                                                    cellClass = 'bg-indigo-50 font-bold text-indigo-600';
                                                    titleText = t('sceneChart.scriptBased');
                                                } else if (isAppearing && isManual) {
                                                    // 手動追加
                                                    symbol = '\u25CB'; // ○
                                                    cellClass = 'bg-amber-50 font-bold text-amber-500';
                                                    cursorClass = isEditable ? 'cursor-pointer hover:bg-amber-100' : '';
                                                } else {
                                                    // 未出演
                                                    symbol = '\u30FB'; // ・
                                                    cellClass = 'text-gray-300';
                                                    cursorClass = isEditable ? 'cursor-pointer hover:bg-gray-100' : '';
                                                }

                                                return (
                                                    <td
                                                        key={char.id}
                                                        className={`px-2 py-4 whitespace-nowrap text-center text-sm border-l border-gray-100 ${cellClass} ${cursorClass}`}
                                                        title={titleText}
                                                        onClick={() => handleCellClick(scene.scene_id, { id: char.id, isAppearing, isManual })}
                                                    >
                                                        {symbol}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>

                    {/* 凡例 */}
                    <div className="flex items-center gap-6 text-sm text-gray-500 px-4">
                        <span className="flex items-center gap-1">
                            <span className="font-bold text-indigo-600">{'\u25CF'}</span> {t('sceneChart.legendScript')}
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="font-bold text-amber-500">{'\u25CB'}</span> {t('sceneChart.legendManual')}
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="text-gray-300">{'\u30FB'}</span> {t('sceneChart.legendNone')}
                        </span>
                    </div>
                </>
            ) : (
                <div className="p-12 text-center border-2 border-dashed border-gray-300 rounded-lg">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7-6h14a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2v-8a2 2 0 012-2z" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">{t('sceneChart.noChartAvailable')}</h3>
                    <p className="mt-1 text-sm text-gray-500">{t('sceneChart.chartAutoGenerated')}</p>
                    {isEditable && (
                        <div className="mt-4 flex justify-center gap-2">
                            <button
                                onClick={() => setShowAddCharModal(true)}
                                className="inline-flex items-center px-3 py-1.5 border border-amber-300 text-sm font-medium rounded-md text-amber-700 bg-amber-50 hover:bg-amber-100"
                            >
                                + {t('sceneChart.addCharacter')}
                            </button>
                            <button
                                onClick={() => setShowAddSceneModal(true)}
                                className="inline-flex items-center px-3 py-1.5 border border-amber-300 text-sm font-medium rounded-md text-amber-700 bg-amber-50 hover:bg-amber-100"
                            >
                                + {t('sceneChart.addScene')}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* カスタムキャラクター追加モーダル */}
            {showAddCharModal && (
                <div className="fixed inset-0 z-50 overflow-y-auto">
                    <div className="flex items-center justify-center min-h-screen px-4">
                        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowAddCharModal(false)} />
                        <div className="relative bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
                            <h3 className="text-lg font-medium mb-4">{t('sceneChart.addCharacter')}</h3>
                            <input
                                type="text"
                                value={newCharName}
                                onChange={e => setNewCharName(e.target.value)}
                                placeholder={t('sceneChart.characterName')}
                                className="w-full border border-gray-300 rounded-md px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                autoFocus
                                onKeyDown={e => {
                                    if (e.key === 'Enter' && newCharName.trim()) {
                                        addCharMutation.mutate(newCharName.trim());
                                    }
                                }}
                            />
                            <div className="flex justify-end gap-2">
                                <button onClick={() => setShowAddCharModal(false)} className="px-3 py-1.5 text-sm text-gray-700 border rounded-md hover:bg-gray-50">
                                    {t('common.cancel')}
                                </button>
                                <button
                                    onClick={() => newCharName.trim() && addCharMutation.mutate(newCharName.trim())}
                                    disabled={!newCharName.trim() || addCharMutation.isPending}
                                    className="px-3 py-1.5 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                                >
                                    {t('common.add')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* カスタムシーン追加モーダル */}
            {showAddSceneModal && (
                <div className="fixed inset-0 z-50 overflow-y-auto">
                    <div className="flex items-center justify-center min-h-screen px-4">
                        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowAddSceneModal(false)} />
                        <div className="relative bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
                            <h3 className="text-lg font-medium mb-4">{t('sceneChart.addScene')}</h3>
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('sceneChart.sceneHeading')}</label>
                                    <input
                                        type="text"
                                        value={newSceneData.heading}
                                        onChange={e => setNewSceneData(d => ({ ...d, heading: e.target.value }))}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        autoFocus
                                    />
                                </div>
                                <div className="flex gap-3">
                                    <div className="flex-1">
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('sceneChart.actNumber')}</label>
                                        <input
                                            type="number"
                                            value={newSceneData.actNumber}
                                            onChange={e => setNewSceneData(d => ({ ...d, actNumber: e.target.value }))}
                                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        />
                                    </div>
                                    <div className="flex-1">
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('sceneChart.sceneNumber')}</label>
                                        <input
                                            type="number"
                                            value={newSceneData.sceneNumber}
                                            onChange={e => setNewSceneData(d => ({ ...d, sceneNumber: e.target.value }))}
                                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-end gap-2 mt-4">
                                <button onClick={() => setShowAddSceneModal(false)} className="px-3 py-1.5 text-sm text-gray-700 border rounded-md hover:bg-gray-50">
                                    {t('common.cancel')}
                                </button>
                                <button
                                    onClick={() => {
                                        if (newSceneData.heading.trim() && newSceneData.sceneNumber) {
                                            addSceneMutation.mutate({
                                                heading: newSceneData.heading.trim(),
                                                act_number: newSceneData.actNumber ? parseInt(newSceneData.actNumber) : null,
                                                scene_number: parseInt(newSceneData.sceneNumber),
                                            });
                                        }
                                    }}
                                    disabled={!newSceneData.heading.trim() || !newSceneData.sceneNumber || addSceneMutation.isPending}
                                    className="px-3 py-1.5 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                                >
                                    {t('common.add')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* シーン編集モーダル */}
            {showEditSceneModal && (
                <div className="fixed inset-0 z-50 overflow-y-auto">
                    <div className="flex items-center justify-center min-h-screen px-4">
                        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowEditSceneModal(null)} />
                        <div className="relative bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
                            <h3 className="text-lg font-medium mb-4">{t('sceneChart.editScene')}</h3>
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('sceneChart.sceneHeading')}</label>
                                    <input
                                        type="text"
                                        value={editSceneData.heading}
                                        onChange={e => setEditSceneData(d => ({ ...d, heading: e.target.value }))}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        autoFocus
                                    />
                                </div>
                                <div className="flex gap-3">
                                    <div className="flex-1">
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('sceneChart.actNumber')}</label>
                                        <input
                                            type="number"
                                            value={editSceneData.actNumber}
                                            onChange={e => setEditSceneData(d => ({ ...d, actNumber: e.target.value }))}
                                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        />
                                    </div>
                                    <div className="flex-1">
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('sceneChart.sceneNumber')}</label>
                                        <input
                                            type="number"
                                            value={editSceneData.sceneNumber}
                                            onChange={e => setEditSceneData(d => ({ ...d, sceneNumber: e.target.value }))}
                                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-between mt-4">
                                <div>
                                    {showEditSceneModal.isCustom && (
                                        <button
                                            onClick={() => {
                                                if (confirm(t('sceneChart.deleteConfirm'))) {
                                                    deleteSceneMutation.mutate(showEditSceneModal.sceneId);
                                                    setShowEditSceneModal(null);
                                                }
                                            }}
                                            className="px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded-md hover:bg-red-50"
                                        >
                                            {t('common.delete')}
                                        </button>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => setShowEditSceneModal(null)} className="px-3 py-1.5 text-sm text-gray-700 border rounded-md hover:bg-gray-50">
                                        {t('common.cancel')}
                                    </button>
                                    <button
                                        onClick={() => {
                                            updateSceneMutation.mutate({
                                                sceneId: showEditSceneModal.sceneId,
                                                data: {
                                                    heading: editSceneData.heading || undefined,
                                                    act_number: editSceneData.actNumber ? parseInt(editSceneData.actNumber) : null,
                                                    scene_number: editSceneData.sceneNumber ? parseInt(editSceneData.sceneNumber) : undefined,
                                                },
                                            });
                                        }}
                                        disabled={updateSceneMutation.isPending}
                                        className="px-3 py-1.5 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                                    >
                                        {t('common.save')}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
