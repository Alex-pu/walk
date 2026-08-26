import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/AppLayout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import AboutPage from "./pages/AboutPage.jsx";
import ActivityPage from "./pages/ActivityPage.jsx";
import ActivityDetailPage from "./pages/ActivityDetailPage.jsx";
import AdminPage from "./pages/AdminPage.jsx";
import CrewDetailPage from "./pages/CrewDetailPage.jsx";
import CrewsPage from "./pages/CrewsPage.jsx";
import CrewInvitePage from "./pages/CrewInvitePage.jsx";
import DiscoverPage from "./pages/DiscoverPage.jsx";
import CrewForumPage from "./pages/CrewForumPage.jsx";
import ForumPage from "./pages/ForumPage.jsx";
import ForumThreadPage from "./pages/ForumThreadPage.jsx";
import ForgotPasswordPage from "./pages/ForgotPasswordPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import OrganizerPage from "./pages/OrganizerPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import ResetPasswordPage from "./pages/ResetPasswordPage.jsx";
import SessionDetailPage from "./pages/SessionDetailPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/join/crew/:crewId" element={<CrewInvitePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="home" element={<HomePage />} />
        <Route path="discover" element={<DiscoverPage />} />
        <Route path="activity" element={<ActivityPage />} />
        <Route path="activities/:activityId" element={<ActivityDetailPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="forum" element={<ForumPage />} />
        <Route path="forum/:threadId" element={<ForumThreadPage />} />
        <Route path="organizer" element={<OrganizerPage />} />
        <Route path="crews" element={<CrewsPage />} />
        <Route path="crews/:crewId" element={<CrewDetailPage />} />
        <Route path="crews/:crewId/forum" element={<CrewForumPage />} />
        <Route path="sessions/:sessionId" element={<SessionDetailPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
