import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { scriptsApi } from '../api/scripts';
import { ArrowLeft, Download } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ScriptDetailPage: React.FC = () => {
    const { t, i18n } = useTranslation();
    const { projectId, scriptId } = useParams<{ projectId: string; scriptId: string }>();

    const { data: script, isLoading } = useQuery({
        queryKey: ['script', scriptId],
        queryFn: () => scriptsApi.getScript(projectId!, scriptId!),
        enabled: !!scriptId,
    });

    const handleDownloadPdf = async () => {
        if (!script) return;
        try {
            const blob = await scriptsApi.downloadScriptPdf(projectId!, scriptId!);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${script.title}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Failed to download PDF', error);
            alert('Failed to download PDF');
        }
    };

    const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);

    const toggleCharacter = (id: string) => {
        if (selectedCharacterId === id) {
            setSelectedCharacterId(null);
        } else {
            setSelectedCharacterId(id);
        }
    };

    if (isLoading) return <div>{t('common.loading')}</div>;
    if (!script) return <div>{t('script.notFound')}</div>;

    return (
        <div className="space-y-6">
            <div className="md:flex md:items-center md:justify-between">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                        <Link to={`/projects/${projectId}/scripts`} className="mr-4 text-gray-500 hover:text-gray-700">
                            <ArrowLeft className="h-6 w-6" />
                        </Link>
                        <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                            {script.title}
                        </h2>
                    </div>
                </div>
                <div className="mt-4 flex md:mt-0 md:ml-4">
                    <button
                        onClick={handleDownloadPdf}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        <Download className="-ml-1 mr-2 h-5 w-5 text-gray-400" />
                        {t('script.downloadPdf')}
                    </button>
                </div>
            </div>

            {/* Metadata Section */}
            {(script.draft_date || script.copyright || script.contact || script.notes || script.revision_text) && (
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">{t('script.metadata')}</h3>
                    </div>
                    <div className="bg-gray-50 px-4 py-5 sm:p-6">
                        <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                            {script.draft_date && (
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">{t('script.draftDate')}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{script.draft_date}</dd>
                                </div>
                            )}
                            {script.revision_text && (
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">{t('script.revision')}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{script.revision_text}</dd>
                                </div>
                            )}
                            {script.copyright && (
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">{t('script.copyright')}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{script.copyright}</dd>
                                </div>
                            )}
                            {script.contact && (
                                <div className="sm:col-span-1">
                                    <dt className="text-sm font-medium text-gray-500">{t('script.contact')}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{script.contact}</dd>
                                </div>
                            )}
                            {script.notes && (
                                <div className="sm:col-span-2">
                                    <dt className="text-sm font-medium text-gray-500">{t('script.notes')}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{script.notes}</dd>
                                </div>
                            )}
                        </dl>
                    </div>
                </div>
            )}

            {/* Character List */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">{t('script.characters') || 'Characters'}</h3>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:p-6">
                    {script.characters && script.characters.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {script.characters.map((character) => (
                                <div
                                    key={character.id}
                                    onClick={() => toggleCharacter(character.id)}
                                    className={`bg-white p-3 rounded shadow-sm border cursor-pointer transition-colors ${selectedCharacterId === character.id
                                        ? 'border-indigo-500 ring-2 ring-indigo-200 bg-indigo-50'
                                        : 'border-gray-200 hover:border-indigo-300'
                                        } flex flex-col justify-center`}
                                >
                                    <div className="flex items-center justify-center">
                                        <span className={`font-bold text-center ${selectedCharacterId === character.id ? 'text-indigo-700' : 'text-gray-900'}`}>
                                            {character.name}
                                        </span>
                                    </div>
                                    {character.description && (
                                        <p className="mt-2 text-xs text-gray-500 text-center border-t pt-2 w-full">
                                            {character.description}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-500 italic">{t('script.noCharacters') || 'No characters found.'}</p>
                    )}
                </div>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">{t('script.content')}</h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        Uploaded by {script.uploaded_at ? new Date(script.uploaded_at).toLocaleString(i18n.language) : t('common.unknown')}
                    </p>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:p-6 font-mono text-sm whitespace-pre-wrap overflow-x-auto">
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
                                        {scene.lines.map((line) => {
                                            const isHighlighted = selectedCharacterId && line.character?.id === selectedCharacterId;
                                            return (
                                                <div key={line.id} className={`grid grid-cols-12 gap-2 p-1 rounded ${isHighlighted ? 'bg-yellow-100' : ''}`}>
                                                    {line.character ? (
                                                        <>
                                                            <div className={`col-span-3 sm:col-span-2 font-bold text-right pr-2 ${isHighlighted ? 'text-indigo-800' : 'text-gray-700'}`}>
                                                                {line.character.name}
                                                            </div>
                                                            <div className={`col-span-9 sm:col-span-10 ${isHighlighted ? 'text-gray-900 font-medium' : 'text-gray-900'}`}>
                                                                {line.content}
                                                            </div>
                                                        </>
                                                    ) : (
                                                        <div className="col-span-12 pl-4 md:pl-0 md:col-start-3 md:col-span-10 text-gray-600 italic">
                                                            {/* Stage Direction (Togaki) */}
                                                            {line.content}
                                                        </div>
                                                    )}
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-500 italic">{t('script.noContent') || 'No parsed content available.'}</p>
                    )}
                </div>
            </div>
        </div>
    );
};
