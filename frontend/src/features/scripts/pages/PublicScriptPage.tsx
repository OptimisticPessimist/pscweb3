import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { scriptsApi } from '../api/scripts';
import { ArrowDownToLine, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';

export const PublicScriptPage: React.FC = () => {
    const { t } = useTranslation();
    const { scriptId } = useParams<{ scriptId: string }>();
    const navigate = useNavigate();
    const [isImporting, setIsImporting] = useState(false);

    const { data: script, isLoading, error } = useQuery({
        queryKey: ['public-script', scriptId],
        queryFn: () => scriptsApi.getPublicScript(scriptId!),
        enabled: !!scriptId,
        retry: false,
    });

    const handleImportScript = async () => {
        if (!scriptId) return;
        if (!confirm(t('script.confirmImport', 'Create a new project using this script?'))) return;

        setIsImporting(true);
        try {
            const project = await scriptsApi.importScript(scriptId);
            toast.success(t('script.importSuccess', 'Project created successfully!'));
            navigate(`/projects/${project.id}/scripts/${project.scripts?.[0]?.id || ''}`); // Navigate to the new project
        } catch (error: any) {
            console.error('Failed to import script', error);
            const message = error.response?.data?.detail || t('script.importFailed', 'Failed to import script');
            toast.error(message);
        } finally {
            setIsImporting(false);
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

    if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin h-8 w-8 text-indigo-500" /></div>;
    if (error || !script) return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('script.notFound')}</h1>
            <p className="text-gray-600">{t('script.publicAccessError', 'This script may effectively not exist or be private.')}</p>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-100 py-10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">

                {/* Header */}
                <div className="md:flex md:items-center md:justify-between bg-white p-6 rounded-lg shadow">
                    <div className="flex-1 min-w-0">
                        <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                            {script.title}
                        </h2>
                        <p className="mt-1 text-sm text-gray-500">
                            by {script.author || t('common.unknown')}
                        </p>
                    </div>
                    <div className="mt-4 flex md:mt-0 md:ml-4">
                        <button
                            onClick={handleImportScript}
                            disabled={isImporting}
                            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                        >
                            {isImporting ? <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" /> : <ArrowDownToLine className="-ml-1 mr-2 h-5 w-5" />}
                            {t('script.importToProject', 'Use this script')}
                        </button>
                    </div>
                </div>

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

                {/* Content */}
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">{t('script.content')}</h3>
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
        </div>
    );
};
