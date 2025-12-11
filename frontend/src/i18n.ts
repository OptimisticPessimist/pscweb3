import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import translationJA from './locales/ja/translation.json';
import translationEN from './locales/en/translation.json';
import translationKO from './locales/ko/translation.json';
import translationZhHans from './locales/zh-Hans/translation.json';
import translationZhHant from './locales/zh-Hant/translation.json';

const resources = {
    ja: { translation: translationJA },
    en: { translation: translationEN },
    ko: { translation: translationKO },
    'zh-Hans': { translation: translationZhHans },
    'zh-Hant': { translation: translationZhHant },
};

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources,
        fallbackLng: 'ja',
        debug: true,
        interpolation: {
            escapeValue: false, // React already escapes values
            prefix: '{',
            suffix: '}',
        },
        detection: {
            order: ['localStorage', 'navigator'],
            caches: ['localStorage'],
        },
    });

export default i18n;
