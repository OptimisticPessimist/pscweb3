import { describe, it, expect, beforeEach } from 'vitest';
import i18n from './i18n';

describe('i18n configuration', () => {
    beforeEach(async () => {
        await i18n.changeLanguage('ja');
    });

    it('should load all language resources', () => {
        const languages = Object.keys(i18n.options.resources || {});
        expect(languages).toContain('ja');
        expect(languages).toContain('en');
        expect(languages).toContain('ko');
        expect(languages).toContain('zh-Hans');
        expect(languages).toContain('zh-Hant');
    });

    it('should have Japanese as default language', () => {
        expect(i18n.options.fallbackLng).toEqual('ja');
    });

    it('should translate keys correctly in Japanese', async () => {
        await i18n.changeLanguage('ja');
        const translated = i18n.t('nav.dashboard');
        expect(translated).toBe('ダッシュボード');
    });

    it('should translate keys correctly in English', async () => {
        await i18n.changeLanguage('en');
        const translated = i18n.t('nav.dashboard');
        expect(translated).toBe('Dashboard');
    });

    it('should translate keys correctly in Korean', async () => {
        await i18n.changeLanguage('ko');
        const translated = i18n.t('nav.dashboard');
        expect(translated).toBe('대시보드');
    });

    it('should translate keys correctly in Simplified Chinese', async () => {
        await i18n.changeLanguage('zh-Hans');
        const translated = i18n.t('nav.dashboard');
        expect(translated).toBe('仪表板');
    });

    it('should translate keys correctly in Traditional Chinese', async () => {
        await i18n.changeLanguage('zh-Hant');
        const translated = i18n.t('nav.dashboard');
        expect(translated).toBe('儀表板');
    });

    it('should change language dynamically', async () => {
        await i18n.changeLanguage('en');
        expect(i18n.language).toBe('en');

        await i18n.changeLanguage('ko');
        expect(i18n.language).toBe('ko');
    });
});
