import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { scriptsApi } from '@/features/scripts/api/scripts';
import { sceneChartsApi } from '@/features/scene_charts/api/sceneCharts';

export const SceneChartPage = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const [selectedScriptId, setSelectedScriptId] = useState<string>('');

    // 1. プロジェクトの脚本一覧を取得
    const { data: scripts, isLoading: scriptsLoading } = useQuery({
        queryKey: ['scripts', projectId],
        queryFn: () => scriptsApi.getScripts(projectId!),
        enabled: !!projectId,
    });

    // 初期ロード時に最新の脚本を選択
    useEffect(() => {
        if (scripts && scripts.length > 0 && !selectedScriptId) {
            console.log('Selecting initial script:', scripts[0]);
            const sortedScripts = [...scripts].sort((a, b) =>
                new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
            );
            setSelectedScriptId(sortedScripts[0].id);
        } else if (scripts && scripts.length > 0 && selectedScriptId) {
            // Validate that selected script still exists
            const exists = scripts.find(s => s.id === selectedScriptId);
            if (!exists) {
                console.warn('Selected script no longer exists, resetting.');
                setSelectedScriptId(scripts[0].id);
            }
        }
    }, [scripts, selectedScriptId]);

    // 3. 選択された脚本の香盤表を取得
    const { data: chart, isLoading: chartLoading } = useQuery({
        queryKey: ['sceneChart', selectedScriptId],
        queryFn: () => sceneChartsApi.getSceneChart(selectedScriptId),
        enabled: !!selectedScriptId,
        retry: false,
    });

    if (scriptsLoading) return <div className="p-8 text-center">Loading scripts...</div>;
    if (!scripts || scripts.length === 0) return (
        <div className="p-8 text-center text-gray-500">
            No scripts uploaded yet. Please upload a script first.
        </div>
    );

    return (
        <div className="space-y-6">
            {/* Header / Config */}
            <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6 flex flex-col sm:flex-row justify-between items-center gap-4">
                <div className="w-full sm:w-auto">
                    <h3 className="text-lg font-medium leading-6 text-gray-900">Scene Chart</h3>
                    {scripts && scripts[0] && (
                        <p className="mt-1 text-sm text-gray-500">
                            Script: {scripts[0].title} (Rev.{scripts[0].revision}) - {new Date(scripts[0].uploaded_at).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </p>
                    )}
                </div>
            </div>

            {/* Matrix View */}
            {chartLoading ? (
                <div className="p-12 text-center text-gray-500">Loading chart...</div>
            ) : chart ? (
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
                                {/* Collect all unique characters from the chart to ensure column consistency */}
                                {/* However, fetching distinct characters from the SCRIPT might be better, but the chart response has structured scenes. */}
                                {/* Let's gather all unique chars from the scenes in the chart to build columns dynamically. */}
                                {(() => {
                                    // Extract unique characters from all scenes for headers
                                    const allCharMap = new Map<string, string>();
                                    chart.scenes.forEach(scene => {
                                        scene.characters.forEach(char => {
                                            allCharMap.set(char.id, char.name);
                                        });
                                    });
                                    // Or utilize script's character list if we fetched script details? 
                                    // Using chart data ensures we only show chars that appear, or we could show all.
                                    // For a true matrix, usually we want ALL characters in the script.
                                    // Since we only have chart data here which lists chars PER scene, 
                                    // we might miss characters that never appear? (Unlikely in a play script context, but possible)
                                    // Ideally we should use script.characters for columns.
                                    // But we don't have full script data here, only summary.
                                    // Let's use the chart's aggregated character set for now.
                                    const uniqueChars = Array.from(allCharMap.entries()).map(([id, name]) => ({ id, name }));

                                    // Sort characters? Maybe by name?
                                    // Ideally specific order.
                                    return uniqueChars.map(char => (
                                        <th key={char.id} scope="col" className="px-2 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                                            <div style={{ writingMode: 'vertical-rl', textOrientation: 'upright' }} className="mx-auto whitespace-nowrap h-32 flex items-center justify-center">
                                                {char.name}
                                            </div>
                                        </th>
                                    ));
                                })()}
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {chart.scenes.map((scene) => (
                                <tr key={scene.scene_number} className="hover:bg-gray-50">
                                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 sticky left-0 bg-white group-hover:bg-gray-50 font-bold border-r border-gray-100">
                                        {scene.act_number ? `#${scene.act_number}` : '-'}
                                    </td>
                                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 sticky left-16 bg-white group-hover:bg-gray-50 font-bold border-r border-gray-100">
                                        #{scene.scene_number}
                                    </td>
                                    <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500 sticky left-36 bg-white group-hover:bg-gray-50 border-r border-gray-200 max-w-xs truncate" title={scene.scene_heading}>
                                        {scene.scene_heading}
                                    </td>
                                    {(() => {
                                        const allCharMap = new Map<string, string>();
                                        chart.scenes.forEach(s => {
                                            s.characters.forEach(c => allCharMap.set(c.id, c.name));
                                        });
                                        const uniqueChars = Array.from(allCharMap.entries()).map(([id, name]) => ({ id, name }));

                                        return uniqueChars.map(char => {
                                            const isAppearing = scene.characters.some(c => c.id === char.id);
                                            return (
                                                <td key={char.id} className={`px-2 py-4 whitespace-nowrap text-center text-sm border-l border-gray-100 ${isAppearing ? 'bg-indigo-50 font-bold text-indigo-600' : 'text-gray-300'}`}>
                                                    {isAppearing ? '●' : '・'}
                                                </td>
                                            );
                                        });
                                    })()}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="p-12 text-center border-2 border-dashed border-gray-300 rounded-lg">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7-6h14a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2v-8a2 2 0 012-2z" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No chart available</h3>
                    <p className="mt-1 text-sm text-gray-500">Charts are automatically generated when you upload a script.</p>
                </div>
            )}
        </div>
    );
};
