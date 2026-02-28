import { Suspense, lazy } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/hooks/useAuth';
import { Toaster } from 'react-hot-toast';
import { HelmetProvider } from 'react-helmet-async';
import './i18n'; // Import i18n configuration

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
const PublicScriptsPage = lazy(() => import('@/features/public_scripts/pages/PublicScriptsPage').then(module => ({ default: module.PublicScriptsPage })));
const PublicScriptDetailPage = lazy(() => import('@/features/public_scripts/pages/PublicScriptDetailPage').then(module => ({ default: module.PublicScriptDetailPage })));
const ManualPage = lazy(() => import('@/pages/ManualPage').then(module => ({ default: module.ManualPage })));
const TicketReservationPage = lazy(() => import('@/features/reservations/pages/TicketReservationPage').then(module => ({ default: module.TicketReservationPage })));
const ReservationCompletedPage = lazy(() => import('@/features/reservations/pages/ReservationCompletedPage').then(module => ({ default: module.ReservationCompletedPage })));
const ReservationListPage = lazy(() => import('@/features/reservations/pages/ReservationListPage').then(module => ({ default: module.ReservationListPage })));
const PublicSchedulePage = lazy(() => import('@/features/reservations/pages/PublicSchedulePage').then(module => ({ default: module.PublicSchedulePage })));
const PublicCalendarPage = lazy(() => import('@/features/reservations/pages/PublicCalendarPage').then(module => ({ default: module.PublicCalendarPage })));  // 🆕
const ReservationCancelPage = lazy(() => import('@/features/reservations/pages/ReservationCancelPage').then(module => ({ default: module.ReservationCancelPage })));

// Schedule Polls
const SchedulePollListPage = lazy(() => import('@/features/schedule_polls/pages/SchedulePollListPage').then(module => ({ default: module.SchedulePollListPage })));
const SchedulePollCreatePage = lazy(() => import('@/features/schedule_polls/pages/SchedulePollCreatePage').then(module => ({ default: module.SchedulePollCreatePage })));
const SchedulePollDetailPage = lazy(() => import('@/features/schedule_polls/pages/SchedulePollDetailPage').then(module => ({ default: module.SchedulePollDetailPage })));
const UserSettingsPage = lazy(() => import('@/pages/auth/UserSettingsPage').then(module => ({ default: module.UserSettingsPage })));

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
    <HelmetProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <Toaster position="top-right" />
            <Suspense fallback={<Loading />}>
              <Routes>
                {/* Public Routes */}
                {/* Public Routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/auth/callback" element={<AuthCallbackPage />} />
                <Route path="/invitations/:token" element={<InvitationLandingPage />} />

                {/* Public Routes with Layout */}
                <Route element={<AppLayout />}>
                  <Route path="/public-scripts" element={<PublicScriptsPage />} />
                  <Route path="/public-scripts/:scriptId" element={<PublicScriptDetailPage />} />
                  <Route path="/manual" element={<ManualPage />} />
                  {/* Reservation Public Pages - might want to exclude AppLayout for immersion or keep it? 
                    User requirement: "Ticket Reservation System". Usually standalone or branded. 
                    Let's put it outside AppLayout or create a specific lightweight layout.
                    For now, I'll put it outside AppLayout to be safe/clean as requested "email only".
                    "without Discord login" -> likely don't want sidebar/header for signed-in users. 
                 */}
                </Route>

                {/* Public Reservation Routes */}
                <Route path="/schedule" element={<PublicSchedulePage />} />
                <Route path="/schedule/calendar" element={<PublicCalendarPage />} />  {/* 🆕 カレンダー表示 */}
                <Route path="/reservations/cancel" element={<ReservationCancelPage />} />
                <Route path="/reservations/completed" element={<ReservationCompletedPage />} />
                <Route path="/reservations/:milestoneId" element={<TicketReservationPage />} />

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
                    <Route path="/projects/:projectId/polls" element={<SchedulePollListPage />} />
                    <Route path="/projects/:projectId/polls/create" element={<SchedulePollCreatePage />} />
                    <Route path="/projects/:projectId/polls/:pollId" element={<SchedulePollDetailPage />} />
                    <Route path="/projects/:projectId/reservations" element={<ReservationListPage />} />
                    <Route path="/projects/:projectId/settings" element={<ProjectSettingsPage />} />
                    <Route path="/settings" element={<UserSettingsPage />} />
                  </Route>
                </Route>

                {/* Default Redirect */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </HelmetProvider>
  );
}

export default App;
