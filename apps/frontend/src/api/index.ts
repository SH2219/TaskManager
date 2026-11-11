import { apiRequest } from "./client";
import type {
  Comment,
  NotificationItem,
  Project,
  ProjectDashboard,
  Tag,
  Task,
  TaskCreateInput,
  TaskUpdateInput,
  User,
} from "./types";

export function listProjects(includeArchived = false) {
  const query = includeArchived ? "?include_archived=true" : "";
  return apiRequest<Project[]>(`/api/projects/${query}`);
}

export function getProject(id: number) {
  return apiRequest<Project>(`/api/projects/${id}`);
}

export function getProjectDashboard(id: number) {
  return apiRequest<ProjectDashboard>(`/api/projects/${id}/dashboard`);
}

export function archiveProject(id: number) {
  return apiRequest<Project>(`/api/projects/${id}/archive`, { method: "POST" });
}

export function restoreProject(id: number) {
  return apiRequest<Project>(`/api/projects/${id}/restore`, { method: "POST" });
}

export function createProject(payload: { name: string; description?: string }) {
  return apiRequest<Project>("/api/projects/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProject(
  id: number,
  payload: { name?: string; description?: string | null },
) {
  return apiRequest<Project>(`/api/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteProject(id: number) {
  return apiRequest<void>(`/api/projects/${id}`, { method: "DELETE" });
}

export function setProjectMembers(id: number, userIds: number[]) {
  return apiRequest<Project>(`/api/projects/${id}/members`, {
    method: "PUT",
    body: JSON.stringify({ user_ids: userIds }),
  });
}

export function listUsers() {
  return apiRequest<User[]>("/api/users/");
}

export function createUser(payload: {
  email: string;
  password: string;
  name?: string;
  phone?: string;
  role?: string;
}) {
  return apiRequest<User>("/api/users/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateUser(
  id: number,
  payload: {
    email?: string;
    name?: string | null;
    phone?: string | null;
    role?: string;
    password?: string;
  },
) {
  return apiRequest<User>(`/api/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteUser(id: number) {
  return apiRequest<void>(`/api/users/${id}`, { method: "DELETE" });
}

export function getMe() {
  return apiRequest<User>("/api/users/me");
}

export function listMyTasks() {
  return apiRequest<Task[]>("/api/users/me/tasks");
}

export function registerUser(payload: {
  email: string;
  password: string;
  name?: string;
  phone?: string;
}) {
  return apiRequest<User>("/api/users/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listTasks(params: {
  project_id?: number;
  top_level_only?: boolean;
  mine?: boolean;
} = {}) {
  const query = new URLSearchParams();
  if (params.project_id) query.set("project_id", String(params.project_id));
  if (params.top_level_only) query.set("top_level_only", "true");
  if (params.mine) query.set("mine", "true");
  const suffix = query.toString() ? `?${query}` : "";
  return apiRequest<Task[]>(`/api/tasks/${suffix}`);
}

export function getTask(id: number) {
  return apiRequest<Task>(`/api/tasks/${id}`);
}

export function createTask(payload: TaskCreateInput) {
  return apiRequest<Task>("/api/tasks/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTask(id: number, payload: TaskUpdateInput) {
  return apiRequest<Task>(`/api/tasks/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTask(id: number) {
  return apiRequest<void>(`/api/tasks/${id}`, { method: "DELETE" });
}

export function completeTask(id: number) {
  return apiRequest<Task>(`/api/tasks/${id}/complete`, { method: "POST" });
}

export function listSubtasks(taskId: number) {
  return apiRequest<Task[]>(`/api/tasks/${taskId}/subtasks`);
}

export function setTaskAssignments(taskId: number, userIds: number[]) {
  return apiRequest<Task>(`/api/tasks/${taskId}/assignments`, {
    method: "PUT",
    body: JSON.stringify({ user_ids: userIds }),
  });
}

export function updateTaskAssignment(
  taskId: number,
  userId: number,
  payload: { progress?: number; rating?: number },
) {
  return apiRequest(`/api/tasks/${taskId}/assignments/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listComments(taskId: number) {
  return apiRequest<Comment[]>(`/api/tasks/${taskId}/comments`);
}

export function createComment(taskId: number, content: string) {
  return apiRequest<Comment>(`/api/tasks/${taskId}/comments`, {
    method: "POST",
    body: JSON.stringify({ task_id: taskId, content }),
  });
}

export function updateComment(commentId: number, content: string) {
  return apiRequest<Comment>(`/api/comments/${commentId}`, {
    method: "PATCH",
    body: JSON.stringify({ content }),
  });
}

export function deleteComment(commentId: number) {
  return apiRequest<void>(`/api/comments/${commentId}`, { method: "DELETE" });
}

export function listTags() {
  return apiRequest<Tag[]>("/api/tags/");
}

export function createTag(payload: { name: string; color?: string; description?: string }) {
  return apiRequest<Tag>("/api/tags", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTag(
  id: number,
  payload: { name?: string; color?: string | null; description?: string | null },
) {
  return apiRequest<Tag>(`/api/tags/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTag(id: number) {
  return apiRequest<void>(`/api/tags/${id}`, { method: "DELETE" });
}

export function generateTaskWithAI(payload: {
  title: string;
  project_id: number;
  priority?: number;
  due_at?: string | null;
  parent_task_id?: number;
}) {
  return apiRequest<{ title: string; description: string; source?: string }>("/api/ai/generate-task", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listNotifications() {
  return apiRequest<NotificationItem[]>("/api/notifications/");
}

export function markNotificationRead(id: number) {
  return apiRequest<NotificationItem>(`/api/notifications/${id}/read`, { method: "POST" });
}

export function markAllNotificationsRead() {
  return apiRequest<NotificationItem[]>("/api/notifications/read-all", { method: "POST" });
}
