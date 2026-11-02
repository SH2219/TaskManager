export type Role = "admin" | "project_lead" | "member";

export type User = {
  id: number;
  email: string;
  name: string | null;
  phone?: string | null;
  role?: Role | string | null;
};

export type Project = {
  id: number;
  name: string;
  description: string | null;
  archived?: boolean;
  member_ids?: number[];
};

export type ProjectDashboard = {
  project_id: number;
  name: string;
  description: string | null;
  archived: boolean;
  progress: number;
  task_count: number;
  completed_count: number;
  open_count: number;
  member_count: number;
};

export type NotificationItem = {
  id: number;
  kind: string;
  title: string;
  body: string;
  task_id: number | null;
  project_id: number | null;
  read_at: string | null;
  created_at: string | null;
};

export type Assignment = {
  user_id: number;
  user_name: string | null;
  user_email: string | null;
  user_role?: string | null;
  progress: number;
  rating: number | null;
};

export type Task = {
  id: number;
  title: string;
  description: string | null;
  project_id: number;
  project_name?: string | null;
  parent_task_id: number | null;
  status: string;
  priority: number | null;
  due_at: string | null;
  assignee_ids: number[];
  assignments: Assignment[];
  tag_ids?: number[];
  comments_count?: number | null;
};

export type Comment = {
  id: number;
  task_id: number;
  user_id?: number | null;
  content: string;
  created_at: string | null;
};

export type Tag = {
  id: number;
  name: string;
  color?: string | null;
  description?: string | null;
};

export type TaskCreateInput = {
  title: string;
  description?: string;
  project_id: number;
  parent_task_id?: number;
  assignee_ids?: number[];
  status?: string;
  priority?: number;
  due_at?: string | null;
};

export type TaskUpdateInput = {
  title?: string;
  description?: string | null;
  status?: string;
  priority?: number;
  due_at?: string | null;
  parent_task_id?: number | null;
};
