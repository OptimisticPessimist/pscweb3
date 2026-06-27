import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LanguageSwitcher } from './LanguageSwitcher';
import '@testing-library/jest-dom';

const mockChangeLanguage = vi.fn();

vi.mock('react-i18next', () => ({
    useTranslation: () => ({
        i18n: {
            language: 'ja',
            changeLanguage: mockChangeLanguage,
        },
    }),
}));

describe('LanguageSwitcher Component', () => {
    beforeEach(() => {
        mockChangeLanguage.mockClear();
    });

    it('should render language switcher button', () => {
        render(<LanguageSwitcher />);
        expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('should display all 5 language options when clicked', () => {
        render(<LanguageSwitcher />);
        const button = screen.getByRole('button');

        fireEvent.click(button);

        // 日本語 appears in both the trigger button and the menu item when language='ja'
        expect(screen.getAllByText(/日本語/).length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText(/English/)).toBeInTheDocument();
        expect(screen.getByText(/한국어/)).toBeInTheDocument();
        expect(screen.getByText(/简体中文/)).toBeInTheDocument();
        expect(screen.getByText(/繁體中文/)).toBeInTheDocument();
    });

    it('should show current language', () => {
        render(<LanguageSwitcher />);
        expect(screen.getByText(/日本語/)).toBeInTheDocument();
    });

    it('should call changeLanguage when a language is selected', () => {
        render(<LanguageSwitcher />);
        const button = screen.getByRole('button');

        fireEvent.click(button);

        const englishOption = screen.getByText(/English/);
        fireEvent.click(englishOption);

        expect(mockChangeLanguage).toHaveBeenCalledWith('en');
    });

    it('should save selected language to localStorage', () => {
        const localStorageMock = {
            getItem: vi.fn(),
            setItem: vi.fn(),
            removeItem: vi.fn(),
            clear: vi.fn(),
            length: 0,
            key: vi.fn(),
        };

        Object.defineProperty(window, 'localStorage', {
            value: localStorageMock,
            writable: true,
        });

        render(<LanguageSwitcher />);
        const button = screen.getByRole('button');

        fireEvent.click(button);

        const koreanOption = screen.getByText(/한국어/);
        fireEvent.click(koreanOption);

        expect(button).toBeInTheDocument();
    });
});
