import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { scriptsApi } from '../api/scripts';
import { ScriptUploadModal } from '../components/ScriptUploadModal';
import { ScriptDetailPage } from './ScriptDetailPage';

export const ScriptsPage = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

    const { data: scripts, isLoading, isError, error } = useQuery({
        queryKey: ['scripts', projectId],
        queryFn: () => scriptsApi.getScripts(projectId!),
        enabled: !!projectId,
    });

    if (isLoading) {
        return <div className="p-4 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500"></div></div>;
    }

    if (isError) {
        return <div className="p-4 text-red-600">Error loading scripts: {error instanceof Error ? error.message : 'Unknown error'}</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-900">Scripts</h2>
                <button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                    {scripts && scripts.length > 0 ? 'Update Script' : 'Upload Script'}
                </button>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-md">
                {scripts && scripts.length > 0 ? (
                    // 1プロジェクト1脚本のため、最初の要素を表示
                    // ScriptDetail コンポーネントを使用（別ファイルからインポートが必要）
                    <div className="p-4 sm:p-6">
                        {/* ScriptDetailPage is imported from ScriptDetailPage */}
                        <ScriptDetailPage />
                    </div>
                ) : (
                    <div className="p-12 text-center text-gray-500">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No script uploaded</h3>
                        <p className="mt-1 text-sm text-gray-500">Upload a Fountain script to get started.</p>
                        <div className="mt-6">
                            <button
                                onClick={() => setIsUploadModalOpen(true)}
                                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                            >
                                Upload Script
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {projectId && (
                <ScriptUploadModal
                    projectId={projectId}
                    isOpen={isUploadModalOpen}
                    onClose={() => setIsUploadModalOpen(false)}
                    initialTitle={scripts && scripts[0] ? scripts[0].title : ''}
                />
            )}
        </div>
    );
};
