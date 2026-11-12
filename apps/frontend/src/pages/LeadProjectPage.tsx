import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  completeTask,
  getProject,
  getProjectDashboard,
  getTask,
  listTasks,
  updateTask,
  updateTaskAssignment,
} from "../api";
import type { Assignment, Project, ProjectDashboard, Task } from "../api/types";
import { ProgressBar, StarRating } from "../components/AssignmentUI";
import { DashboardPanel } from "../components/Dashboard";
import { Sheet } from "../components/Sheet";
import { formatDate, statusLabel } from "../lib/format";
import { notify } from "../lib/notify";

type Step = "choose" | "progress" | "status" | "details" | "confirm";

export default function LeadProjectPage() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const [project, setProject] = useState<Project | null>(null);
  const [dashboard, setDashboard] = useState<ProjectDashboard | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<Task | null>(null);
  const [step, setStep] = useState<Step>("choose");
  const [drafts, setDrafts] = useState<Assignment[]>([]);
  const [status, setStatus] = useState("todo");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [proj, taskList, board] = await Promise.all([
        getProject(id),
        listTasks({ project_id: id, top_level_only: false }),
        getProjectDashboard(id),
      ]);
      setProject(proj);
      setTasks(taskList);
      setDashboard(board);
    } catch (err) {
      setProject(null);
      notify.fromError(err, "This project is not assigned to you");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  function openTask(task: Task) {
    setActive(task);
    setStep("choose");
    setDrafts(task.assignments ?? []);
    setStatus(task.status === "done" ? "todo" : task.status);
  }

  function closeSheet() {
    setActive(null);
    setStep("choose");
  }

  async function refreshTask(taskId: number) {
    const updated = await getTask(taskId);
    setActive(updated);
    setDrafts(updated.assignments ?? []);
    setTasks((prev) => prev.map((task) => (task.id === updated.id ? updated : task)));
    setDashboard(await getProjectDashboard(id));
    return updated;
  }

  async function saveProgress() {
    if (!active) return;
    setSaving(true);
    try {
      const original = new Map((active.assignments ?? []).map((item) => [item.user_id, item]));
      for (const draft of drafts) {
        const before = original.get(draft.user_id);
        const payload: { progress?: number; rating?: number } = {};
        if (!before || before.progress !== draft.progress) payload.progress = draft.progress;
        if (draft.rating && draft.rating !== before?.rating) payload.rating = draft.rating;
        if (payload.progress != null || payload.rating != null) {
          await updateTaskAssignment(active.id, draft.user_id, payload);
        }
      }
      await refreshTask(active.id);
      notify.success("Progress saved.");
      setStep("confirm");
    } catch (err) {
      notify.fromError(err, "Could not save progress");
    } finally {
      setSaving(false);
    }
  }

  async function saveStatus() {
    if (!active) return;
    setSaving(true);
    try {
      await updateTask(active.id, { status });
      await refreshTask(active.id);
      notify.success("Status updated.");
      setStep("confirm");
    } catch (err) {
      notify.fromError(err, "Could not update status");
    } finally {
      setSaving(false);
    }
  }

  async function markCompleted() {
    if (!active) return;
    setSaving(true);
    try {
      await completeTask(active.id);
      await load();
      notify.success("Task marked completed. The project dashboard is updated.");
      closeSheet();
    } catch (err) {
      notify.fromError(err, "Could not mark the task completed");
    } finally {
      setSaving(false);
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
        <p className="muted">Project not found.</p>
        <Link to="/projects">Back to assigned projects</Link>
      </div>
    );
  }

  return (
    <div className="page">
      <Link to="/projects" className="back-link">
        ← Assigned projects
      </Link>

      <DashboardPanel
        eyebrow="Project dashboard"
        title={project.name}
        note={project.description}
        progress={dashboard?.progress ?? 0}
        progressLabel="complete"
        stats={[
          { label: "Open", value: dashboard?.open_count ?? 0 },
          { label: "Completed", value: dashboard?.completed_count ?? 0 },
          { label: "Tasks", value: dashboard?.task_count ?? 0 },
        ]}
      />

      <section className="stack">
        <h2>Choose a task</h2>
        {tasks.length === 0 ? (
          <p className="card empty muted">No tasks in this project yet.</p>
        ) : (
          <ul className="task-list">
            {tasks.map((task) => (
              <li key={task.id}>
                <button type="button" className="task-card-main" onClick={() => openTask(task)}>
                  <span className="task-card-head">
                    <strong>{task.title}</strong>
                    <span className={`badge badge-${task.status}`}>{statusLabel(task.status)}</span>
                  </span>
                  <span className="task-meta">
                    <span>{formatDate(task.due_at)}</span>
                    {task.parent_task_id ? <span>Subtask</span> : null}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {active && (
        <Sheet title={active.title} onClose={closeSheet}>
          {step === "choose" && (
            <div className="choice-list">
              <p className="flow-step-label">Choose action</p>
              <button type="button" className="choice" onClick={() => setStep("progress")}>
                <strong>Update progress</strong>
                <span>Move each person's progress, then save.</span>
              </button>
              <button type="button" className="choice" onClick={() => setStep("status")}>
                <strong>Update task status</strong>
                <span>Set the task to to do or in progress.</span>
              </button>
              <button type="button" className="choice" onClick={() => setStep("details")}>
                <strong>View task details</strong>
                <span>Read the description, priority, and due date.</span>
              </button>
            </div>
          )}

          {step === "progress" && (
            <div className="form-stack">
              <p className="flow-step-label">Update progress</p>
              {drafts.length === 0 ? (
                <p className="muted">Nobody is assigned to this task yet.</p>
              ) : (
                drafts.map((assignment) => (
                  <div key={assignment.user_id} className="assignment-item">
                    <strong>{assignment.user_name || assignment.user_email}</strong>
                    <label className="progress-field">
                      Progress ({assignment.progress}%)
                      <input
                        type="range"
                        min={0}
                        max={100}
                        value={assignment.progress}
                        onChange={(event) => {
                          const progress = Number(event.target.value);
                          setDrafts((prev) =>
                            prev.map((item) =>
                              item.user_id === assignment.user_id ? { ...item, progress } : item,
                            ),
                          );
                        }}
                      />
                      <ProgressBar value={assignment.progress} />
                    </label>
                    <div className="rating-field">
                      <span className="field-label">Rating</span>
                      <StarRating
                        value={assignment.rating}
                        onChange={(rating) =>
                          setDrafts((prev) =>
                            prev.map((item) =>
                              item.user_id === assignment.user_id ? { ...item, rating } : item,
                            ),
                          )
                        }
                      />
                    </div>
                  </div>
                ))
              )}
              <div className="form-row">
                <button type="button" className="btn btn-primary" disabled={saving} onClick={saveProgress}>
                  {saving ? "Saving…" : "Save changes"}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setStep("choose")}>
                  Back
                </button>
              </div>
            </div>
          )}

          {step === "status" && (
            <div className="form-stack">
              <p className="flow-step-label">Update task status</p>
              {active.status === "done" && <p className="muted">This task is already completed.</p>}
              <label>
                Status
                <select value={status} onChange={(event) => setStatus(event.target.value)}>
                  <option value="todo">To do</option>
                  <option value="in_progress">In progress</option>
                </select>
              </label>
              <div className="form-row">
                <button type="button" className="btn btn-primary" disabled={saving} onClick={saveStatus}>
                  {saving ? "Saving…" : "Save changes"}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setStep("choose")}>
                  Back
                </button>
              </div>
            </div>
          )}

          {step === "details" && (
            <div className="form-stack">
              <p className="flow-step-label">Task details</p>
              <p>{active.description || "No description."}</p>
              <p className="muted">
                {statusLabel(active.status)} · Priority {active.priority ?? 3} · {formatDate(active.due_at)}
              </p>
              <ul className="list">
                {(active.assignments ?? []).map((assignment) => (
                  <li key={assignment.user_id}>
                    <strong>{assignment.user_name || assignment.user_email}</strong>
                    <span className="muted"> {assignment.progress}%</span>
                    <ProgressBar value={assignment.progress} />
                  </li>
                ))}
              </ul>
              <button type="button" className="btn btn-ghost" onClick={() => setStep("choose")}>
                Back to actions
              </button>
            </div>
          )}

          {step === "confirm" && (
            <div className="form-stack">
              <p className="flow-step-label">Project progress updated</p>
              <p>
                This project is now at <strong>{dashboard?.progress ?? 0}%</strong>.
              </p>
              <h3>Task completed?</h3>
              <div className="form-row">
                <button type="button" className="btn btn-primary" disabled={saving} onClick={markCompleted}>
                  {saving ? "Saving…" : "Yes, mark completed"}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setStep("choose")}>
                  Not yet
                </button>
              </div>
            </div>
          )}
        </Sheet>
      )}
    </div>
  );
}
