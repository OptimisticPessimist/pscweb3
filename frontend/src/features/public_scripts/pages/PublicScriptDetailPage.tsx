
import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { publicScriptsApi } from '../api/publicScripts';
import { ArrowLeft, Info, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const PublicScriptDetailPage: React.FC = () => {
    const { t, i18n } = useTranslation();
    const { scriptId } = useParams<{ scriptId: string }>();
    const navigate = useNavigate();

    const { data: script, isLoading, error } = useQuery({
        queryKey: ['publicScript', scriptId],
        queryFn: () => publicScriptsApi.getPublicScript(scriptId!),
        enabled: !!scriptId,
    });

    if (isLoading) return <div className="p-6">{t('common.loading')}</div>;
    if (error || !script) return <div className="p-6">{t('script.notFound')}</div>;

    const handleCreateProject = () => {
        navigate('/dashboard', {
            state: {
                importScriptId: script.id,
                importScriptTitle: script.title
            }
        });
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
            {/* Header */}
            <div className="md:flex md:items-center md:justify-between">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                        <Link to="/public-scripts" className="mr-4 text-gray-500 hover:text-gray-700">
                            <ArrowLeft className="h-6 w-6" />
                        </Link>
                        <div>
                            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                                {script.title}
                            </h2>
                            <p className="mt-1 text-sm text-gray-500">
                                {script.author ? `by ${script.author}` : t('common.unknownAuthor')} • {new Date(script.uploaded_at).toLocaleString(i18n.language)}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="mt-4 flex md:mt-0 md:ml-4">
                    <button
                        onClick={handleCreateProject}
                        className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        <Plus className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                        {t('publicScript.createProject') || "Create Project"}
                    </button>
                </div>
            </div>

            {/* Metadata Card */}
            {(script.public_terms || script.public_contact || script.notes) && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <Info className="h-5 w-5 text-blue-400" aria-hidden="true" />
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-blue-800">
                                {t('publicScript.usageInfo') || "Usage Information"}
                            </h3>
                            <div className="mt-2 text-sm text-blue-700 space-y-2">
                                {script.public_terms && (
                                    <div>
                                        <span className="font-semibold">{t('publicScript.terms') || "Terms"}:</span> {script.public_terms}
                                    </div>
                                )}
                                {script.public_contact && (
                                    <div>
                                        <span className="font-semibold">{t('publicScript.contact') || "Contact"}:</span> {script.public_contact}
                                    </div>
                                )}
                                {script.notes && (
                                    <div>
                                        <span className="font-semibold">{t('script.notes') || "Notes"}:</span> {script.notes}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Content Preview */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200 flex justify-between items-center">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">{t('script.content')}</h3>
                    <div className="text-sm text-gray-500">
                        {t('publicScript.previewOnly') || "Preview Mode"}
                    </div>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:p-6 font-mono text-sm whitespace-pre-wrap overflow-x-auto">
                    {/* Reuse Scene/Line rendering logic or simplified view */}
                    {script.scenes.length > 0 ? (
                        <div className="space-y-4">
                            {script.scenes.map((scene) => (
                                <div key={scene.id} className="space-y-2">
                                    <h4 className="font-bold text-gray-800 uppercase">
                                        {scene.scene_number}. {scene.heading}
                                    </h4>
                                    {scene.description && (
                                        <p className="text-gray-600 italic whitespace-pre-wrap">{scene.description}</p>
                                    )}
                                    <div className="space-y-1 pl-4 border-l-2 border-gray-200">
                                        {scene.lines.map((line) => (
                                            <div key={line.id} className="grid grid-cols-12 gap-2 p-1 rounded">
                                                {line.character ? (
                                                    <>
                                                        <div className="col-span-3 sm:col-span-2 font-bold text-right pr-2 text-gray-700">
                                                            {line.character.name}
                                                        </div>
                                                        <div className="col-span-9 sm:col-span-10 text-gray-900">
                                                            {line.content}
                                                        </div>
                                                    </>
                                                ) : (
                                                    <div className="col-span-12 pl-4 md:pl-0 md:col-start-3 md:col-span-10 text-gray-600 italic">
                                                        {line.content}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-500 italic">{t('script.noContent')}</p>
                    )}
                </div>
            </div>
        </div>
    );
};
