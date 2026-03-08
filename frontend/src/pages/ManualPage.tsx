import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, UserCircle2 } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';
import { Fragment } from 'react';
import { getCommonContent, getRoleContent, getDetailedFeatures, MANUAL_ROLES, type ManualRole } from './manualContent';

// Helper to map role ID to i18n key for labels
const roleLabelMap: Record<ManualRole, string> = {
    producer: 'producer',
    director: 'director',
    playwright: 'playwright',
    'ad-sm': 'adSm',
    cast: 'cast',
    'tech-staff': 'techStaff',
};

// Recommended permissions for each role
const suggestedPermissions: Record<ManualRole, string[]> = {
    producer: ['owner'],
    director: ['owner', 'editor'],
    playwright: ['editor'],
    'ad-sm': ['editor'],
    cast: ['viewer'],
    'tech-staff': ['viewer'],
};

export function ManualPage() {
    const { t, i18n } = useTranslation();
    const [searchParams, setSearchParams] = useSearchParams();
    const currentLanguage = i18n.language;

    // Handle initial role from query param
    const roleParam = searchParams.get('role') as ManualRole;
    const initialIndex = MANUAL_ROLES.includes(roleParam)
        ? MANUAL_ROLES.indexOf(roleParam)
        : 0;

    const commonContent = getCommonContent(currentLanguage);
    const detailedFeatures = getDetailedFeatures(currentLanguage);

    const handleTabChange = (index: number) => {
        setSearchParams({ role: MANUAL_ROLES[index] }, { replace: true });
    };

    const renderMarkdown = (content: string) => (
        <div className="prose prose-gray max-w-none
            prose-headings:font-bold
            prose-h1:text-4xl prose-h1:mb-8 prose-h1:pb-4 prose-h1:border-b
            prose-h2:text-3xl prose-h2:mt-16 prose-h2:mb-8
            prose-h3:text-2xl prose-h3:mt-12 prose-h3:mb-6
            prose-h4:text-xl prose-h4:mt-10 prose-h4:mb-4
            prose-p:my-5 prose-p:leading-relaxed prose-p:text-gray-700
            prose-ul:my-5 prose-ul:pl-8 prose-ul:list-disc
            prose-ol:my-5 prose-ol:pl-8 prose-ol:list-decimal
            prose-li:my-2
            prose-table:my-6
            prose-th:bg-gray-100 prose-th:p-3 prose-th:border
            prose-td:p-3 prose-td:border
            prose-blockquote:bg-blue-50 prose-blockquote:border-l-4 prose-blockquote:border-blue-400 prose-blockquote:p-6 prose-blockquote:my-8 prose-blockquote:rounded-r-lg
            prose-a:text-blue-600 prose-a:hover:text-blue-800 prose-a:font-semibold prose-a:no-underline prose-a:hover:underline
            prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-rose-600 before:content-none after:content-none
            prose-hr:my-16 prose-hr:border-gray-200
        ">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
            </ReactMarkdown>
        </div>
    );

    return (
        <div id="manual-top" className="min-h-screen bg-gray-50 pb-20">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            to="/dashboard"
                            className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors p-2 -ml-2 rounded-lg hover:bg-gray-100"
                        >
                            <ArrowLeft className="w-5 h-5" />
                            <span className="hidden sm:inline font-medium">{t('common.back')}</span>
                        </Link>
                        <h1 className="text-xl font-bold text-gray-900 tracking-tight">{t('manual.title')}</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-8">
                {/* Introduction (Common) */}
                <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 sm:p-12 mb-10 overflow-hidden">
                    {renderMarkdown(commonContent)}
                </section>

                {/* Role Selector */}
                <div className="mb-10">
                    <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2.5">
                        <UserCircle2 className="w-6 h-6 text-blue-600" />
                        {t('manual.selectRole')}
                    </h2>

                    <TabGroup defaultIndex={initialIndex} onChange={handleTabChange}>
                        {/* Tab List */}
                        <div className="overflow-x-auto pb-4 scrollbar-hide -mx-2 px-2">
                            <TabList className="flex gap-3 min-w-max">
                                {MANUAL_ROLES.map((role) => (
                                    <Tab as={Fragment} key={role}>
                                        {({ selected }) => (
                                            <button
                                                className={`px-6 py-3 rounded-xl text-sm font-bold transition-all whitespace-nowrap outline-none ring-offset-2 focus-visible:ring-2 focus-visible:ring-blue-500
                                                    ${selected
                                                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-200 -translate-y-0.5'
                                                        : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                                    }`}
                                            >
                                                {t(`manual.roles.${roleLabelMap[role]}`)}
                                            </button>
                                        )}
                                    </Tab>
                                ))}
                            </TabList>
                        </div>

                        {/* Content Panels */}
                        <TabPanels className="mt-6">
                            {MANUAL_ROLES.map((role) => (
                                <TabPanel key={role} className="outline-none">
                                    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 sm:p-12">
                                        {/* Suggested Permissions Badge */}
                                        <div className="flex flex-wrap items-center gap-4 mb-10 border-b border-gray-100 pb-10">
                                            <span className="text-sm font-bold text-gray-500 uppercase tracking-widest">
                                                {t('manual.recommendedPermission')}:
                                            </span>
                                            <div className="flex gap-2.5">
                                                {suggestedPermissions[role].map(perm => (
                                                    <span
                                                        key={perm}
                                                        className={`px-4 py-1.5 rounded-lg text-xs font-black uppercase tracking-wider
                                                            ${perm === 'owner' ? 'bg-amber-100 text-amber-700 ring-1 ring-amber-300' :
                                                                perm === 'editor' ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-300' :
                                                                    'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-300'}`}
                                                    >
                                                        {t(`manual.permissions.${perm}`)}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Role specific content */}
                                        {renderMarkdown(getRoleContent(role, currentLanguage))}
                                    </div>
                                </TabPanel>
                            ))}
                        </TabPanels>
                    </TabGroup>
                </div>

                {/* Detailed Features Section */}
                {detailedFeatures && (
                    <section className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 sm:p-12 mt-12 mb-20 bg-gradient-to-br from-white to-gray-50">
                        {renderMarkdown(detailedFeatures)}
                    </section>
                )}
            </main>
        </div>
    );
}
