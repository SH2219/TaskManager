import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  createComment,
  createTask,
  deleteComment,
  deleteTask,
  generateTaskWithAI,
  getProject,
  getProjectDashboard,
  listComments,
  listSubtasks,
  listTasks,
  listUsers,
  setProjectMembers,
  setTaskAssignments,
  updateProject,
  updateTask,
  archiveProject,
  restoreProject,
} from "../api";
import type { Comment, Project, ProjectDashboard, Task, User } from "../api/types";
import { UserMultiSelect } from "../components/AssignmentUI";
import { DashboardPanel } from "../components/Dashboard";
import { Sheet } from "../components/Sheet";
import { formatDate, statusLabel } from "../lib/format";

const STATUSES = ["todo", "in_progress", "done"] as const;

export default function AdminProjectPage() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const [project, setProject] = useState<Project | null>(null);
  const [dashboard, setDashboard] = useState<ProjectDashboard | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [memberIds, setMemberIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [savingProject, setSavingProject] = useState(false);
  const [title, setTitle] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [priority, setPriority] = useState(3);
  const [dueAt, setDueAt] = useState("");
  const [parentId, setParentId] = useState<number | "">("");
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [generating, setGenerating] = useState(false);
  const [selected, setSelected] = useState<Task | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editPriority, setEditPriority] = useState(3);
  const [editDue, setEditDue] = useState("");
  const [editStatus, setEditStatus] = useState("todo");
  const [editAssignees, setEditAssignees] = useState<number[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentText, setCommentText] = useState("");
  const [subtasks, setSubtasks] = useState<Record<number, Task[]>>({});
  const [panel, setPanel] = useState<"edit" | "members" | "create" | null>(null);
  const [sheetError, setSheetError] = useState("");
  const [savingTask, setSavingTask] = useState(false);

  const load = useCallback(async (opts?: { quiet?: boolean }) => {
    if (!id) return;
    if (!opts?.quiet) setLoading(true);
    setError("");
    try {
      const [proj, taskList, userList, board] = await Promise.all([
        getProject(id),
        listTasks({ project_id: id, top_level_only: true }),
        listUsers(),
        getProjectDashboard(id),
      ]);
      setProject(proj);
      setName(proj.name);
      setDescription(proj.description ?? "");
      setMemberIds(proj.member_ids ?? []);
      setTasks(taskList);
      setUsers(userList);
      setDashboard(board);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
      if (!opts?.quiet) setProject(null);
    } finally {
      if (!opts?.quiet) setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const team = users.filter((person) => (project?.member_ids ?? []).includes(person.id));

  function taskAssigneeIds(task: Task) {
    if (task.assignee_ids?.length) return task.assignee_ids;
    return (task.assignments ?? []).map((item) => item.user_id);
  }

  function openEditProject() {
    if (!project) return;
    setSelected(null);
    setName(project.name);
    setDescription(project.description ?? "");
    setPanel("edit");
  }

  function openMembers() {
    if (!project) return;
    setSelected(null);
    setMemberIds(project.member_ids ?? []);
    setPanel("members");
  }

  function openCreateTask() {
    setSelected(null);
    setTitle("");
    setTaskDescription("");
    setParentId("");
    setAssigneeIds([]);
    setDueAt("");
    setPriority(3);
    setPanel("create");
  }

  function closePanel() {
    setPanel(null);
    if (project) {
      setName(project.name);
      setDescription(project.description ?? "");
      setMemberIds(project.member_ids ?? []);
    }
  }

  function closeTaskSheet() {
    setSelected(null);
    setSheetError("");
    setCommentText("");
  }

  async function handleSaveProject(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setSavingProject(true);
    setError("");
    try {
      const updated = await updateProject(id, {
        name: name.trim(),
        description: description.trim() || null,
      });
      setProject(updated);
      closePanel();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the project");
    } finally {
      setSavingProject(false);
    }
  }

  async function handleMembers() {
    setError("");
    setNotice("");
    try {
      const updated = await setProjectMembers(id, memberIds);
      setProject(updated);
      setMemberIds(updated.member_ids ?? []);
      setNotice("Project members saved.");
      closePanel();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save members");
    }
  }

  async function handleArchive() {
    if (!project) return;
    setError("");
    try {
      const updated = project.archived ? await restoreProject(id) : await archiveProject(id);
      setProject(updated);
      closePanel();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not archive the project");
    }
  }

  async function handleGenerate() {
    if (!title.trim() || !id) return;
    setGenerating(true);
    setError("");
    try {
      const result = await generateTaskWithAI({
        title: title.trim(),
        project_id: id,
        priority,
        due_at: dueAt || undefined,
        parent_task_id: parentId === "" ? undefined : parentId,
      });
      setTitle(result.title);
      setTaskDescription(result.description);
      if (result.source === "fallback") {
        setNotice("AI was unavailable, so a local draft was filled in. Edit it before saving.");
      } else {
        setNotice("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate a description");
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateEdit() {
    if (!editTitle.trim() || !id || !selected) return;
    setGenerating(true);
    setSheetError("");
    try {
      const result = await generateTaskWithAI({
        title: editTitle.trim(),
        project_id: id,
        priority: editPriority,
        due_at: editDue || undefined,
        parent_task_id: selected.parent_task_id ?? undefined,
      });
      setEditTitle(result.title);
      setEditDescription(result.description);
    } catch (err) {
      setSheetError(err instanceof Error ? err.message : "Could not generate a description");
    } finally {
      setGenerating(false);
    }
  }

  async function handleCreateTask(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setError("");
    setNotice("");
    try {
      await createTask({
        title: title.trim(),
        description: taskDescription.trim() || undefined,
        project_id: id,
        parent_task_id: parentId === "" ? undefined : parentId,
        assignee_ids: assigneeIds.filter((uid) => (project?.member_ids ?? []).includes(uid)),
        priority,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
      });
      const assigned = assigneeIds.length > 0;
      setTitle("");
      setTaskDescription("");
      setParentId("");
      setAssigneeIds([]);
      setDueAt("");
      setPriority(3);
      if (assigned) setNotice("Task created. New assignees get a task assigned notification.");
      closePanel();
      await load({ quiet: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the task");
    }
  }

  async function openTask(task: Task) {
    setPanel(null);
    setSheetError("");
    setSelected(task);
    setEditTitle(task.title);
    setEditDescription(task.description ?? "");
    setEditPriority(task.priority ?? 3);
    setEditStatus(task.status);
    setEditDue(task.due_at ? task.due_at.slice(0, 10) : "");
    setEditAssignees(taskAssigneeIds(task));
    setCommentText("");
    setComments([]);
    try {
      setComments(await listComments(task.id));
    } catch (err) {
      setSheetError(err instanceof Error ? err.message : "Could not load comments");
    }
  }

  async function handleSaveTask(event: FormEvent) {
    event.preventDefault();
    if (!selected || !editTitle.trim()) return;
    setSheetError("");
    setSavingTask(true);
    try {
      const members = project?.member_ids ?? memberIds;
      const updated = await updateTask(selected.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
        priority: editPriority,
        status: editStatus,
        due_at: editDue ? new Date(`${editDue}T12:00:00`).toISOString() : null,
      });
      await setTaskAssignments(
        updated.id,
        editAssignees.filter((uid) => members.includes(uid)),
      );
      setNotice("Task saved. New assignees get a task assigned notification.");
      closeTaskSheet();
      await load({ quiet: true });
    } catch (err) {
      setSheetError(err instanceof Error ? err.message : "Could not save the task");
    } finally {
      setSavingTask(false);
    }
  }

  async function handleDeleteTask(taskId: number) {
    if (!confirm("Delete this task?")) return;
    try {
      await deleteTask(taskId);
      if (selected?.id === taskId) closeTaskSheet();
      await load({ quiet: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the task");
    }
  }

  async function toggleSubtasks(taskId: number) {
    if (subtasks[taskId]) {
      setSubtasks((prev) => {
        const next = { ...prev };
        delete next[taskId];
        return next;
      });
      return;
    }
    setSubtasks((prev) => ({ ...prev, [taskId]: [] }));
    try {
      const children = await listSubtasks(taskId);
      setSubtasks((prev) => ({ ...prev, [taskId]: children }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load subtasks");
    }
  }

  async function handleAddComment(event: FormEvent) {
    event.preventDefault();
    if (!selected || !commentText.trim()) return;
    setSheetError("");
    try {
      await createComment(selected.id, commentText.trim());
      setCommentText("");
      setComments(await listComments(selected.id));
    } catch (err) {
      setSheetError(err instanceof Error ? err.message : "Could not post comment");
    }
  }

  async function handleDeleteComment(commentId: number) {
    if (!selected) return;
    setSheetError("");
    try {
      await deleteComment(commentId);
      setComments(await listComments(selected.id));
    } catch (err) {
      setSheetError(err instanceof Error ? err.message : "Could not delete comment");
    }
  }

  if (loading) {
    return (
      <div className="page">
        <p className="muted">Loading project…</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="page">
        <div className="alert alert-error">{error || "Project not found."}</div>
        <Link to="/projects">Back to projects</Link>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <div className="row-between">
          <Link to="/projects" className="back-link">
            ← Projects
          </Link>
          {project.archived && <span className="badge">Archived</span>}
        </div>
      </header>
      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-ok">{notice}</div>}

      {dashboard && (
        <DashboardPanel
          eyebrow="Overview"
          title={project.name}
          note={project.description || "Edit the project, add the team, then assign the work."}
          progress={dashboard.progress}
          progressLabel="complete"
          stats={[
            { label: "Open", value: dashboard.open_count },
            { label: "Done", value: dashboard.completed_count },
            { label: "Team", value: dashboard.member_count },
          ]}
        />
      )}

      <section className="card">
        <div className="row-between">
          <div>
            <h2>Setup</h2>
            <p className="muted">Edit details, add the team, then create tasks.</p>
          </div>
        </div>
        <div className="project-actions">
          <button type="button" className="btn btn-ghost" onClick={openEditProject}>
            Edit project
          </button>
          <button type="button" className="btn btn-ghost" onClick={openMembers}>
            Members{team.length ? ` (${team.length})` : ""}
          </button>
          <button type="button" className="btn btn-primary" onClick={openCreateTask}>
            Create task
          </button>
        </div>
        {team.length > 0 ? (
          <ul className="people-list">
            {team.map((person) => (
              <li key={person.id} className="muted">
                {person.name?.trim() || person.email}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No members yet. Add a lead and people before assigning work.</p>
        )}
      </section>

      <section className="card">
        <div className="row-between">
          <h2>Tasks ({tasks.length})</h2>
          <button type="button" className="btn btn-primary btn-sm" onClick={openCreateTask}>
            Create task
          </button>
        </div>
        {tasks.length === 0 ? (
          <p className="muted">No tasks yet.</p>
        ) : (
          <ul className="task-list">
            {tasks.map((task) => (
              <li key={task.id} className="task-card">
                <div className="task-card-main">
                  <span className="task-card-head">
                    <strong>{task.title}</strong>
                    <span className={`badge badge-${task.status}`}>{statusLabel(task.status)}</span>
                  </span>
                  <span className="task-meta">
                    <span>Priority {task.priority ?? 3}</span>
                    <span>{formatDate(task.due_at)}</span>
                    {task.assignments?.length ? <span>{task.assignments.length} assigned</span> : null}
                  </span>
                </div>
                <div className="project-actions">
                  <button type="button" className="btn btn-primary btn-sm" onClick={() => openTask(task)}>
                    Edit
                  </button>
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => toggleSubtasks(task.id)}>
                    {subtasks[task.id] ? "Hide subtasks" : "Subtasks"}
                  </button>
                  <button type="button" className="btn btn-danger btn-sm" onClick={() => handleDeleteTask(task.id)}>
                    Delete
                  </button>
                </div>
                {subtasks[task.id] && (
                  <ul className="subtask-list">
                    {subtasks[task.id].length === 0 ? (
                      <li className="muted">No subtasks.</li>
                    ) : (
                      subtasks[task.id].map((child) => (
                        <li key={child.id} className="row-between">
                          <button type="button" className="task-title-btn" onClick={() => openTask(child)}>
                            {child.title}
                          </button>
                          <button type="button" className="btn btn-ghost btn-sm" onClick={() => openTask(child)}>
                            Edit
                          </button>
                        </li>
                      ))
                    )}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {panel === "edit" && (
        <Sheet title="Edit project" onClose={closePanel}>
          <form className="form-stack" onSubmit={handleSaveProject}>
            <label>
              Name
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              Description
              <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
            </label>
            <div className="form-row">
              <button type="submit" className="btn btn-primary" disabled={savingProject}>
                {savingProject ? "Saving…" : "Save changes"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={handleArchive}>
                {project.archived ? "Restore" : "Archive"}
              </button>
            </div>
          </form>
        </Sheet>
      )}

      {panel === "members" && (
        <Sheet title="Project members" onClose={closePanel}>
          <p className="muted">
            Include at least one project lead so someone can update progress on this project. Promote people
            to lead on Users first if you need more leads.
          </p>
          <UserMultiSelect
            users={users}
            selectedIds={memberIds}
            onChange={setMemberIds}
            label="People on this project"
            hint="Leads are listed first. Members can only see tasks after you assign them."
          />
          <button type="button" className="btn btn-primary" onClick={handleMembers}>
            Save members
          </button>
        </Sheet>
      )}

      {panel === "create" && (
        <Sheet title="Create task" onClose={closePanel}>
          <form className="form-stack" onSubmit={handleCreateTask}>
            <input placeholder="Task title" value={title} onChange={(e) => setTitle(e.target.value)} required />
            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleGenerate}
              disabled={generating || !title.trim()}
            >
              {generating ? "Generating…" : "Generate description"}
            </button>
            <textarea
              rows={4}
              placeholder="Description"
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
            />
            <div className="form-row">
              <label>
                Priority
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                />
              </label>
              <label>
                Due date
                <input type="date" value={dueAt} onChange={(e) => setDueAt(e.target.value)} />
              </label>
            </div>
            <label>
              Parent task
              <select
                value={parentId}
                onChange={(e) => setParentId(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">None</option>
                {tasks.map((task) => (
                  <option key={task.id} value={task.id}>
                    {task.title}
                  </option>
                ))}
              </select>
            </label>
            {team.length > 0 ? (
              <UserMultiSelect
                users={team}
                selectedIds={assigneeIds}
                onChange={setAssigneeIds}
                label="Assign to"
              />
            ) : (
              <p className="muted">Add project members before assigning tasks.</p>
            )}
            <button type="submit" className="btn btn-primary">
              Create task
            </button>
          </form>
        </Sheet>
      )}

      {selected && (
        <Sheet title="Edit task" onClose={closeTaskSheet}>
          {sheetError && <div className="alert alert-error">{sheetError}</div>}
          <form className="form-stack" onSubmit={handleSaveTask}>
            <label>
              Title
              <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} required />
            </label>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleGenerateEdit}
              disabled={generating || !editTitle.trim()}
            >
              {generating ? "Generating…" : "Generate description"}
            </button>
            <label>
              Description
              <textarea rows={4} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
            </label>
            <label>
              Status
              <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                {STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {statusLabel(status)}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-row">
              <label>
                Priority
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={editPriority}
                  onChange={(e) => setEditPriority(Number(e.target.value))}
                />
              </label>
              <label>
                Due date
                <input type="date" value={editDue} onChange={(e) => setEditDue(e.target.value)} />
              </label>
            </div>
            {team.length > 0 ? (
              <UserMultiSelect
                users={team}
                selectedIds={editAssignees}
                onChange={setEditAssignees}
                label="Assign to project members"
              />
            ) : (
              <p className="muted">Add project members before assigning people to this task.</p>
            )}
            <p className="muted">Saving a new assignee sends them a task assigned notification.</p>
            <button type="submit" className="btn btn-primary" disabled={savingTask}>
              {savingTask ? "Saving…" : "Save task"}
            </button>
          </form>
          <h3>Comments</h3>
          <form className="form-row" onSubmit={handleAddComment}>
            <input
              placeholder="Write a comment"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
            />
            <button type="submit" className="btn btn-primary btn-sm">
              Post
            </button>
          </form>
          <ul className="comment-list">
            {comments.map((comment) => (
              <li key={comment.id} className="comment-item">
                <p>{comment.content}</p>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => handleDeleteComment(comment.id)}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        </Sheet>
      )}
    </div>
  );
}
