import React, { Suspense, lazy } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/hooks/useAuth';
import { Toaster } from 'react-hot-toast';
import './i18n'; // Import i18n configuration
import { LoginPage } from '@/pages/auth/LoginPage';
import { AuthCallbackPage } from '@/pages/auth/AuthCallbackPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { ProjectDetailsPage } from '@/features/projects/ProjectDetailsPage';
import { ProtectedLayout } from '@/layouts/ProtectedLayout';
import { AppLayout } from '@/layouts/AppLayout';
import { Loading } from '@/components/Loading';

// Lazy load pages
const LoginPage = lazy(() => import('@/pages/auth/LoginPage').then(module => ({ default: module.LoginPage })));
const AuthCallbackPage = lazy(() => import('@/pages/auth/AuthCallbackPage').then(module => ({ default: module.AuthCallbackPage })));
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage').then(module => ({ default: module.DashboardPage })));
const ProjectDetailsPage = lazy(() => import('@/features/projects/ProjectDetailsPage').then(module => ({ default: module.ProjectDetailsPage })));
const ScriptListPage = lazy(() => import('./features/scripts/pages/ScriptListPage').then(module => ({ default: module.ScriptListPage })));
const ScriptUploadPage = lazy(() => import('./features/scripts/pages/ScriptUploadPage').then(module => ({ default: module.ScriptUploadPage })));
const ScriptDetailPage = lazy(() => import('./features/scripts/pages/ScriptDetailPage').then(module => ({ default: module.ScriptDetailPage })));
const SceneChartPage = lazy(() => import('@/features/scene_charts/pages/SceneChartPage').then(module => ({ default: module.SceneChartPage })));
const CastingPage = lazy(() => import('@/features/casting/pages/CastingPage').then(module => ({ default: module.CastingPage })));
const StaffPage = lazy(() => import('@/features/staff').then(module => ({ default: module.StaffPage })));
const SchedulePage = lazy(() => import('@/features/schedule/pages/SchedulePage').then(module => ({ default: module.SchedulePage })));
const AttendancePage = lazy(() => import('@/features/attendance/AttendancePage').then(module => ({ default: module.AttendancePage })));
const ProjectSettingsPage = lazy(() => import('@/features/projects/pages/ProjectSettingsPage').then(module => ({ default: module.ProjectSettingsPage })));
const InvitationLandingPage = lazy(() => import('./features/projects/pages/InvitationLandingPage').then(module => ({ default: module.InvitationLandingPage })));
const MySchedulePage = lazy(() => import('@/features/schedule/MySchedulePage').then(module => ({ default: module.MySchedulePage })));

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
          <Toaster position="top-right" />
          <Suspense fallback={<Loading />}>
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
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
