import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, UserCircle2 } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';
import { Fragment } from 'react';
import { getCommonContent, getRoleContent, MANUAL_ROLES, type ManualRole } from './manualContent';

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

    const handleTabChange = (index: number) => {
        setSearchParams({ role: MANUAL_ROLES[index] }, { replace: true });
    };

    const renderMarkdown = (content: string) => (
        <div className="prose prose-gray max-w-none
            prose-headings:font-bold
            prose-h1:text-3xl prose-h1:mb-4 prose-h1:pb-2 prose-h1:border-b
            prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4
            prose-h3:text-xl prose-h3:mt-6 prose-h3:mb-3
            prose-p:my-3 prose-p:leading-relaxed
            prose-ul:my-3 prose-ul:pl-6
            prose-ol:my-3 prose-ol:pl-6
            prose-li:my-1
            prose-table:my-4
            prose-th:bg-gray-100 prose-th:p-2 prose-th:border
            prose-td:p-2 prose-td:border
            prose-blockquote:bg-blue-50 prose-blockquote:border-l-4 prose-blockquote:border-blue-400 prose-blockquote:p-4 prose-blockquote:my-4
            prose-a:text-blue-600 prose-a:hover:underline
            prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded
            prose-hr:my-8
        ">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
            </ReactMarkdown>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            to="/dashboard"
                            className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                            <span className="hidden sm:inline font-medium">{t('common.back')}</span>
                        </Link>
                        <h1 className="text-xl font-bold text-gray-900">{t('manual.title')}</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-8">
                {/* Introduction (Common) */}
                <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
                    {renderMarkdown(commonContent)}
                </section>

                {/* Role Selector */}
                <div className="mb-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <UserCircle2 className="w-5 h-5 text-blue-600" />
                        {t('manual.selectRole')}
                    </h2>

                    <TabGroup defaultIndex={initialIndex} onChange={handleTabChange}>
                        {/* Tab List with horizontal scroll on mobile */}
                        <div className="overflow-x-auto pb-2 scrollbar-hide -mx-2 px-2">
                            <TabList className="flex gap-2 min-w-max">
                                {MANUAL_ROLES.map((role) => (
                                    <Tab as={Fragment} key={role}>
                                        {({ selected }) => (
                                            <button
                                                className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all whitespace-nowrap outline-none
                                                    ${selected
                                                        ? 'bg-blue-600 text-white shadow-md'
                                                        : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
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
                        <TabPanels className="mt-8">
                            {MANUAL_ROLES.map((role) => (
                                <TabPanel key={role} className="outline-none">
                                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
                                        {/* Suggested Permissions Badge */}
                                        <div className="flex flex-wrap items-center gap-3 mb-8 border-b border-gray-100 pb-6">
                                            <span className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                                {t('manual.recommendedPermission')}:
                                            </span>
                                            <div className="flex gap-2">
                                                {suggestedPermissions[role].map(perm => (
                                                    <span
                                                        key={perm}
                                                        className={`px-3 py-1 rounded-md text-xs font-bold uppercase
                                                            ${perm === 'owner' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
                                                                perm === 'editor' ? 'bg-blue-100 text-blue-700 border border-blue-200' :
                                                                    'bg-emerald-100 text-emerald-700 border border-emerald-200'}`}
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
            </main>
        </div>
    );
}
