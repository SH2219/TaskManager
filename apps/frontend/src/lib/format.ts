import type { Role } from "../api/types";

export function roleLabel(role?: string | null) {
  if (role === "admin") return "Admin";
  if (role === "project_lead") return "Project lead";
  if (role === "member") return "Member";
  return "Member";
}

export function homePath(role?: string | null) {
  if (role === "admin") return "/admin";
  if (role === "project_lead") return "/projects";
  return "/my-tasks";
}

export function isRole(role: string | null | undefined, expected: Role) {
  return role === expected;
}

export function statusLabel(status: string) {
  if (status === "in_progress") return "In progress";
  if (status === "todo") return "To do";
  if (status === "done") return "Done";
  return status;
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "No due date";
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}
