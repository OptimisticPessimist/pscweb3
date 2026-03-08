import { commonJa } from './common/ja';
import { commonEn } from './common/en';
import { commonKo } from './common/ko';
import { commonZhHans } from './common/zh-Hans';
import { commonZhHant } from './common/zh-Hant';

import { detailedFeaturesJa } from './common/detailed_features_ja';
import { detailedFeaturesEn } from './common/detailed_features_en';

import { producerJa } from './roles/producer/ja';
import { producerEn } from './roles/producer/en';
import { producerKo } from './roles/producer/ko';
import { producerZhHans } from './roles/producer/zh-Hans';
import { producerZhHant } from './roles/producer/zh-Hant';

import { directorJa } from './roles/director/ja';
import { directorEn } from './roles/director/en';
import { directorKo } from './roles/director/ko';
import { directorZhHans } from './roles/director/zh-Hans';
import { directorZhHant } from './roles/director/zh-Hant';

import { playwrightJa } from './roles/playwright/ja';
import { playwrightEn } from './roles/playwright/en';
import { playwrightKo } from './roles/playwright/ko';
import { playwrightZhHans } from './roles/playwright/zh-Hans';
import { playwrightZhHant } from './roles/playwright/zh-Hant';

import { adSmJa } from './roles/ad-sm/ja';
import { adSmEn } from './roles/ad-sm/en';
import { adSmKo } from './roles/ad-sm/ko';
import { adSmZhHans } from './roles/ad-sm/zh-Hans';
import { adSmZhHant } from './roles/ad-sm/zh-Hant';

import { castJa } from './roles/cast/ja';
import { castEn } from './roles/cast/en';
import { castKo } from './roles/cast/ko';
import { castZhHans } from './roles/cast/zh-Hans';
import { castZhHant } from './roles/cast/zh-Hant';

import { techStaffJa } from './roles/tech-staff/ja';
import { techStaffEn } from './roles/tech-staff/en';
import { techStaffKo } from './roles/tech-staff/ko';
import { techStaffZhHans } from './roles/tech-staff/zh-Hans';
import { techStaffZhHant } from './roles/tech-staff/zh-Hant';

// Manual Role Type
export type ManualRole = 'producer' | 'director' | 'playwright' | 'ad-sm' | 'cast' | 'tech-staff';

// Role Order Definition
export const MANUAL_ROLES: ManualRole[] = [
    'producer', 'director', 'playwright', 'ad-sm', 'cast', 'tech-staff'
];

// Common Content Map
const commonContentMap: Record<string, string> = {
    ja: commonJa,
    en: commonEn,
    ko: commonKo,
    'zh-Hans': commonZhHans,
    'zh-Hant': commonZhHant,
};

// Role Content Map
const roleContentMap: Record<ManualRole, Record<string, string>> = {
    producer: { ja: producerJa, en: producerEn, ko: producerKo, 'zh-Hans': producerZhHans, 'zh-Hant': producerZhHant },
    director: { ja: directorJa, en: directorEn, ko: directorKo, 'zh-Hans': directorZhHans, 'zh-Hant': directorZhHant },
    playwright: { ja: playwrightJa, en: playwrightEn, ko: playwrightKo, 'zh-Hans': playwrightZhHans, 'zh-Hant': playwrightZhHant },
    'ad-sm': { ja: adSmJa, en: adSmEn, ko: adSmKo, 'zh-Hans': adSmZhHans, 'zh-Hant': adSmZhHant },
    cast: { ja: castJa, en: castEn, ko: castKo, 'zh-Hans': castZhHans, 'zh-Hant': castZhHant },
    'tech-staff': { ja: techStaffJa, en: techStaffEn, ko: techStaffKo, 'zh-Hans': techStaffZhHans, 'zh-Hant': techStaffZhHant },
};

// Detailed Features Content Map
const detailedContentMap: Record<string, string> = {
    ja: detailedFeaturesJa,
    en: detailedFeaturesEn,
    // Add other languages as they are implemented
};

export function getDetailedFeatures(lang: string): string {
    return detailedContentMap[lang] || detailedContentMap['en'] || detailedFeaturesJa;
}

export function getCommonContent(lang: string): string {
    return commonContentMap[lang] || commonContentMap['en'] || commonJa;
}

export function getRoleContent(role: ManualRole, lang: string): string {
    const roleResources = roleContentMap[role];
    if (!roleResources) return '';
    return roleResources[lang] || roleResources['en'] || roleResources['ja'] || '';
}

// Temporary export for backward compatibility until ManualPage is fully updated
export { commonJa as manualJa, commonEn as manualEn, commonKo as manualKo, commonZhHans as manualZhHans, commonZhHant as manualZhHant };
