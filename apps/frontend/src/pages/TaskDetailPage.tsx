import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getTask } from "../api";
import type { Task } from "../api/types";
import { ProgressBar } from "../components/AssignmentUI";
import { useAuth } from "../context/AuthContext";
import { formatDate, roleLabel, statusLabel } from "../lib/format";

export default function TaskDetailPage() {
  const { taskId } = useParams();
  const id = Number(taskId);
  const { user } = useAuth();
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getTask(id)
      .then(setTask)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not open this task"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="page">
        <p className="muted">Loading task…</p>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="page">
        <div className="alert alert-error">{error || "Task not found."}</div>
        <Link to="/my-tasks">Back to assigned tasks</Link>
      </div>
    );
  }

  const mine = task.assignments?.find((item) => item.user_id === user?.id);

  return (
    <div className="page">
      <header className="page-header">
        <Link to="/my-tasks" className="back-link">
          ← Assigned tasks
        </Link>
        <h1>{task.title}</h1>
        <p className="muted">{task.project_name || "Task details"}</p>
      </header>
      <section className="card">
        <p className="flow-step-label">View task details</p>
        <p>{task.description || "No description yet."}</p>
        <div className="meta-row">
          <span className={`badge badge-${task.status}`}>{statusLabel(task.status)}</span>
          <span className="meta-chip">Priority {task.priority ?? 3}</span>
          <span className="meta-chip">{formatDate(task.due_at)}</span>
        </div>
        {mine && (
          <div className="progress-field">
            <span>Your progress ({mine.progress}%)</span>
            <ProgressBar value={mine.progress} />
          </div>
        )}
        {user?.role === "project_lead" && (
          <Link className="btn btn-primary" to={`/projects/${task.project_id}`}>
            Update this project
          </Link>
        )}
      </section>
      <section className="card">
        <h2>People on this task</h2>
        {(task.assignments ?? []).length === 0 ? (
          <p className="muted">No one is assigned.</p>
        ) : (
          <ul className="list">
            {task.assignments.map((assignment) => (
              <li key={assignment.user_id} className="list-item">
                <div>
                  <strong>{assignment.user_name || assignment.user_email}</strong>
                  <p className="muted">{roleLabel(assignment.user_role)} · {assignment.progress}%</p>
                  <ProgressBar value={assignment.progress} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
