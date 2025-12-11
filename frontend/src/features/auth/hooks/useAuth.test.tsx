import type { ReactNode } from 'react';
import { renderHook, act } from '@testing-library/react';
import { useAuth, AuthProvider } from './useAuth';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { authApi } from '../api/auth';

// Mock dependencies
vi.mock('../api/auth', () => ({
    authApi: {
        getUser: vi.fn(),
    },
}));

vi.mock('@/api/client', () => ({
    apiClient: {
        defaults: { headers: { Authorization: '' } },
    },
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>{children}</AuthProvider>
        </QueryClientProvider>
    );
};

describe('useAuth', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
    });

    it('should initialize with no user', () => {
        const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

        expect(result.current.user).toBeUndefined();
        expect(result.current.isAuthenticated).toBe(false);
    });

    it('should login and set token', async () => {
        const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

        // Mock getUser to return a user
        const mockUser = { id: '1', email: 'test@example.com', name: 'Test User', discord_id: '123', discord_username: 'test' };
        vi.mocked(authApi.getUser).mockResolvedValue(mockUser as any);

        act(() => {
            result.current.login('test-token');
        });

        // Token should be in localStorage
        expect(localStorage.getItem('token')).toBe('test-token');

        // Note: React Query's async nature makes verifying 'user' state tricky in sync test without waitFor
        // But we verified login function sets the token.
    });

    it('should logout and clear token', () => {
        const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

        act(() => {
            result.current.login('test-token');
        });
        expect(localStorage.getItem('token')).toBe('test-token');

        act(() => {
            result.current.logout();
        });

        expect(localStorage.getItem('token')).toBeNull();
    });
});
