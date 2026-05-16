import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { Globe } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const languages = [
    { code: 'ja', name: '日本語', flag: '🇯🇵' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'ko', name: '한국어', flag: '🇰🇷' },
    { code: 'zh-Hans', name: '简体中文', flag: '🇨🇳' },
    { code: 'zh-Hant', name: '繁體中文', flag: '🇹🇼' },
];

export function LanguageSwitcher() {
    const { i18n } = useTranslation();

    const currentLanguage = languages.find((lang) => lang.code === i18n.language) || languages[0];

    const handleLanguageChange = (languageCode: string) => {
        i18n.changeLanguage(languageCode);
    };

    return (
        <Menu as="div" className="relative">
            <MenuButton className="flex items-center gap-2 p-2 rounded-full hover:bg-gray-100 transition-colors">
                <Globe className="w-5 h-5 text-gray-600" />
                <span className="text-sm font-medium text-gray-700 hidden sm:inline">
                    {currentLanguage.flag} {currentLanguage.name}
                </span>
            </MenuButton>

            <MenuItems className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                <div className="py-1">
                    {languages.map((language) => (
                        <MenuItem key={language.code}>
                            {({ focus }) => (
                                <button
                                    onClick={() => handleLanguageChange(language.code)}
                                    className={`${focus ? 'bg-purple-50' : ''
                                        } ${i18n.language === language.code ? 'bg-purple-100 font-semibold' : ''
                                        } flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 transition-colors`}
                                >
                                    <span className="text-xl">{language.flag}</span>
                                    <span>{language.name}</span>
                                </button>
                            )}
                        </MenuItem>
                    ))}
                </div>
            </MenuItems>
        </Menu>
    );
}
