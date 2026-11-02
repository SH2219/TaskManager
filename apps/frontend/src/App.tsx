import { type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { PrivateRoute, PublicRoute } from "./components/Layout";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { homePath } from "./lib/format";
import LoginPage from "./pages/LoginPage";
import MyTasksPage from "./pages/MyTasksPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import ProjectsPage from "./pages/ProjectsPage";
import RegisterPage from "./pages/RegisterPage";
import TagsPage from "./pages/TagsPage";
import TaskDetailPage from "./pages/TaskDetailPage";
import AdminHomePage from "./pages/AdminHomePage";
import UsersPage from "./pages/UsersPage";

function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={homePath(user?.role)} replace />;
}

function AdminOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "admin") return <HomeRedirect />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<PublicRoute />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
          <Route element={<PrivateRoute />}>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/admin" element={<AdminOnly><AdminHomePage /></AdminOnly>} />
            <Route path="/users" element={<AdminOnly><UsersPage /></AdminOnly>} />
            <Route path="/tags" element={<AdminOnly><TagsPage /></AdminOnly>} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            <Route path="/my-tasks" element={<MyTasksPage />} />
            <Route path="/tasks/:taskId" element={<TaskDetailPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
