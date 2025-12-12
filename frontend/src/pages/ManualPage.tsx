import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

// Import manual content for each language
import { manualJa, manualEn, manualKo, manualZhHans, manualZhHant } from './manualContent';

// Map language codes to manual content
const manualContent: Record<string, string> = {
    ja: manualJa,
    en: manualEn,
    ko: manualKo,
    'zh-Hans': manualZhHans,
    'zh-Hant': manualZhHant,
};

export function ManualPage() {
    const { t, i18n } = useTranslation();
    const currentLanguage = i18n.language;

    // Get the appropriate manual content, fallback to English then Japanese
    const content = manualContent[currentLanguage] || manualContent['en'] || manualJa;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="max-w-4xl mx-auto flex items-center gap-4">
                    <Link
                        to="/dashboard"
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span>{t('common.back')}</span>
                    </Link>
                </div>
            </header>

            {/* Content */}
            <main className="max-w-4xl mx-auto px-6 py-8">
                <article className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
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
                </article>
            </main>
        </div>
    );
}
