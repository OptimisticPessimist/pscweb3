import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scriptsApi } from '../api/scripts';
import { FileText, Download, Trash2, Plus, Eye } from 'lucide-react';

export const ScriptListPage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();

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
            const blob = await scriptsApi.downloadScriptPdf(projectId!, scriptId);
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
    };

    if (isLoading) return <div>Loading scripts...</div>;

    return (
        <div className="space-y-6">
            <div className="sm:flex sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Scripts</h2>
                    <p className="mt-1 text-sm text-gray-500">
                        Manage your Fountain scripts and screenplays.
                    </p>
                </div>
                <div className="mt-4 sm:mt-0">
                    <Link
                        to={`/projects/${projectId}/scripts/upload`}
                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        <Plus className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                        Upload Script
                    </Link>
                </div>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul role="list" className="divide-y divide-gray-200">
                    {scripts?.length === 0 && (
                        <li className="px-4 py-12 text-center text-gray-500">
                            No scripts found. Upload one to get started!
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
                                        onClick={() => handleDownloadPdf(script.id, script.title)}
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
        </div>
    );
};
