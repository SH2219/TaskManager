import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AdminProjectPage from "./AdminProjectPage";
import LeadProjectPage from "./LeadProjectPage";

export default function ProjectDetailPage() {
  const { user } = useAuth();
  if (user?.role === "admin") return <AdminProjectPage />;
  if (user?.role === "project_lead") return <LeadProjectPage />;
  return <Navigate to="/my-tasks" replace />;
}
