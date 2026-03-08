
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scriptsApi } from '../api/scripts';
import { FileText, Download, Trash2, Plus, Eye } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ScriptListPage: React.FC = () => {
    const { t } = useTranslation();
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();

    const [pdfOptionsTarget, setPdfOptionsTarget] = useState<{ scriptId: string; title: string } | null>(null);
    const [pdfOrientation, setPdfOrientation] = useState<string>('landscape');
    const [pdfWritingDirection, setPdfWritingDirection] = useState<string>('vertical');

    const { data: scripts, isLoading } = useQuery({
        queryKey: ['scripts', projectId],
        queryFn: () => scriptsApi.getScripts(projectId!),
        enabled: !!projectId,
    });

    const deleteMutation = useMutation({
        mutationFn: (scriptId: string) => scriptsApi.deleteScript(projectId!, scriptId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['scripts', projectId] });
        },
        onError: (error: Error) => {
            alert(`Failed to delete script: ${error.message || 'Unknown error'}`);
        }
    });

    const handleDownloadPdf = async (scriptId: string, title: string) => {
        try {
            const blob = await scriptsApi.downloadScriptPdf(projectId!, scriptId, {
                orientation: pdfOrientation,
                writingDirection: pdfWritingDirection,
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${title}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Failed to download PDF', error);
            alert('Failed to download PDF');
        }
        setPdfOptionsTarget(null);
    };

    if (isLoading) return <div>Loading scripts...</div>;

    return (
        <div className="space-y-6">
            <div className="sm:flex sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">{t('script.title')}</h2>
                    <p className="mt-1 text-sm text-gray-500">
                        {t('script.manageScripts')}
                    </p>
                </div>
                <div className="mt-4 sm:mt-0">
                    <Link
                        to={`/projects/${projectId}/scripts/upload`}
                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        <Plus className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                        {t('script.upload')}
                    </Link>
                </div>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul role="list" className="divide-y divide-gray-200">
                    {scripts?.length === 0 && (
                        <li className="px-4 py-12 text-center text-gray-500">
                            {t('script.uploadToGetStarted')}
                        </li>
                    )}
                    {scripts?.map((script) => (
                        <li key={script.id}>
                            <div className="px-4 py-4 sm:px-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
                                <div className="flex items-center min-w-0 flex-1">
                                    <div className="flex-shrink-0">
                                        <FileText className="h-10 w-10 text-gray-400" />
                                    </div>
                                    <div className="min-w-0 flex-1 px-4 md:grid md:grid-cols-2 md:gap-4">
                                        <div>
                                            <p className="text-sm font-medium text-indigo-600 truncate">{script.title}</p>
                                            <p className="mt-2 flex items-center text-xs text-gray-500">
                                                <span className="truncate">Rev.{script.revision}</span>
                                                <span className="mx-1">&bull;</span>
                                                <span>{new Date(script.uploaded_at).toLocaleDateString()}</span>
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-4">
                                    <Link
                                        to={`/projects/${projectId}/scripts/${script.id}`}
                                        className="text-gray-400 hover:text-gray-500"
                                        title="View Script"
                                    >
                                        <Eye className="h-5 w-5" />
                                    </Link>
                                    <button
                                        onClick={() => setPdfOptionsTarget({ scriptId: script.id, title: script.title })}
                                        className="text-gray-400 hover:text-gray-500"
                                        title="Download PDF"
                                    >
                                        <Download className="h-5 w-5" />
                                    </button>
                                    <button
                                        onClick={() => {
                                            if (window.confirm('Are you sure you want to delete this script?')) {
                                                deleteMutation.mutate(script.id);
                                            }
                                        }}
                                        className="text-red-400 hover:text-red-500"
                                        title="Delete Script"
                                    >
                                        <Trash2 className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            {/* PDF Options Modal */}
            {pdfOptionsTarget && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
                    <div className="bg-white rounded-lg shadow-xl p-6 w-80 space-y-4">
                        <h3 className="text-lg font-medium text-gray-900">{t('script.pdfOptions')}</h3>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('script.pdfOrientation')}
                            </label>
                            <select
                                value={pdfOrientation}
                                onChange={(e) => setPdfOrientation(e.target.value)}
                                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                            >
                                <option value="landscape">{t('script.pdfLandscape')}</option>
                                <option value="portrait">{t('script.pdfPortrait')}</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('script.pdfWritingDirection')}
                            </label>
                            <select
                                value={pdfWritingDirection}
                                onChange={(e) => setPdfWritingDirection(e.target.value)}
                                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                            >
                                <option value="vertical">{t('script.pdfVertical')}</option>
                                <option value="horizontal">{t('script.pdfHorizontal')}</option>
                            </select>
                        </div>
                        <div className="flex justify-end space-x-2 pt-2">
                            <button
                                onClick={() => setPdfOptionsTarget(null)}
                                className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                            >
                                {t('common.cancel')}
                            </button>
                            <button
                                onClick={() => handleDownloadPdf(pdfOptionsTarget.scriptId, pdfOptionsTarget.title)}
                                className="px-4 py-2 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
                            >
                                {t('script.downloadPdf')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
