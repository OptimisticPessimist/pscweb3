import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/hooks/useAuth';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AuthCallbackPage } from '@/pages/auth/AuthCallbackPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { ProjectDetailsPage } from '@/features/projects/ProjectDetailsPage';
import { ProtectedLayout } from '@/layouts/ProtectedLayout';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />

            {/* Protected Routes */}
            <Route element={<ProtectedLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/projects/:projectId" element={<ProjectDetailsPage />}>
                {/* Nested routes will be added later */}
              </Route>
            </Route>

            {/* Default Redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
