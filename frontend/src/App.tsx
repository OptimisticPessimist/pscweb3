import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/hooks/useAuth';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AuthCallbackPage } from '@/pages/auth/AuthCallbackPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { ProjectDetailsPage } from '@/features/projects/ProjectDetailsPage';
import { ProtectedLayout } from '@/layouts/ProtectedLayout';
import { AppLayout } from '@/layouts/AppLayout';
import { SceneChartPage } from '@/features/scene_charts/pages/SceneChartPage';
import { CastingPage } from '@/features/casting/pages/CastingPage';
import { StaffPage } from '@/features/staff';
import { SchedulePage } from '@/features/schedule/pages/SchedulePage';
import { ProjectSettingsPage } from '@/features/projects/pages/ProjectSettingsPage';
import { InvitationLandingPage } from './features/projects/pages/InvitationLandingPage';
import { ScriptListPage } from './features/scripts/pages/ScriptListPage';
import { ScriptUploadPage } from './features/scripts/pages/ScriptUploadPage';
import { ScriptDetailPage } from './features/scripts/pages/ScriptDetailPage';
import { MySchedulePage } from '@/features/schedule/MySchedulePage';
import { AttendancePage } from '@/features/attendance/AttendancePage';

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
            <Route path="/invitations/:token" element={<InvitationLandingPage />} />

            {/* Protected Routes */}
            <Route element={<ProtectedLayout />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/my-schedule" element={<MySchedulePage />} />
                <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
                <Route path="/projects/:projectId/scripts" element={<ScriptListPage />} />
                <Route path="/projects/:projectId/scripts/upload" element={<ScriptUploadPage />} />
                <Route path="/projects/:projectId/scripts/:scriptId" element={<ScriptDetailPage />} />
                <Route path="/projects/:projectId/chart" element={<SceneChartPage />} />
                <Route path="/projects/:projectId/cast" element={<CastingPage />} />
                <Route path="/projects/:projectId/staff" element={<StaffPage />} />
                <Route path="/projects/:projectId/schedule" element={<SchedulePage />} />
                <Route path="/projects/:projectId/attendance" element={<AttendancePage />} />
                <Route path="/projects/:projectId/settings" element={<ProjectSettingsPage />} />
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
