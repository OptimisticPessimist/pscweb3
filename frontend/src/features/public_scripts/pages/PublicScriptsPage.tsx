
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { publicScriptsApi } from '../api/publicScripts';
import { Link } from 'react-router-dom';
import { BookOpen } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const PublicScriptsPage: React.FC = () => {
    const { t, i18n } = useTranslation();

    const { data, isLoading } = useQuery({
        queryKey: ['publicScripts'],
        queryFn: () => publicScriptsApi.getPublicScripts(),
    });

    if (isLoading) return <div className="p-6">{t('common.loading')}</div>;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="md:flex md:items-center md:justify-between mb-6">
                <div className="flex-1 min-w-0">
                    <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                        {t('publicScript.title') || "Public Scripts"}
                    </h2>
                    <p className="mt-1 text-sm text-gray-500">
                        {t('publicScript.description') || "Explore scripts shared by the community."}
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data?.scripts.map((script) => (
                    <Link
                        key={script.id}
                        to={`/public-scripts/${script.id}`}
                        className="block hover:shadow-lg transition-shadow duration-200"
                    >
                        <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-200 h-full flex flex-col">
                            <div className="px-4 py-5 sm:p-6 flex-1">
                                <div className="flex items-center mb-2">
                                    <BookOpen className="h-5 w-5 text-indigo-500 mr-2" />
                                    <h3 className="text-lg font-medium text-gray-900 truncate">
                                        {script.title}
                                    </h3>
                                </div>
                                <p className="text-sm text-gray-500 mb-4 line-clamp-3">
                                    {script.author ? `by ${script.author}` : t('common.unknownAuthor')}
                                </p>
                                {script.public_terms && (
                                    <div className="text-xs text-gray-400 bg-gray-50 p-2 rounded truncate mb-2">
                                        {script.public_terms}
                                    </div>
                                )}
                                {script.notes && (
                                    <div className="text-xs text-gray-400 italic truncate">
                                        {script.notes}
                                    </div>
                                )}
                            </div>
                            <div className="bg-gray-50 px-4 py-4 sm:px-6">
                                <div className="text-xs text-gray-500">
                                    {new Date(script.uploaded_at).toLocaleDateString(i18n.language)}
                                </div>
                            </div>
                        </div>
                    </Link>
                ))}
                {(!data?.scripts || data.scripts.length === 0) && (
                    <div className="col-span-full text-center py-12 text-gray-500">
                        {t('publicScript.noScripts') || "No public scripts found."}
                    </div>
                )}
            </div>
        </div>
    );
};
