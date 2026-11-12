import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMyTasks } from "../api";
import type { Task } from "../api/types";
import { ProgressBar } from "../components/AssignmentUI";
import { useAuth } from "../context/AuthContext";
import { formatDate, statusLabel } from "../lib/format";
import { notify } from "../lib/notify";

export default function MyTasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listMyTasks()
      .then(setTasks)
      .catch((err) => notify.fromError(err, "Failed to load tasks"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Assigned tasks</h1>
        <p className="muted">
          {user?.role === "member"
            ? "Open a task to see the details. Status and progress are updated by the project lead."
            : "Work assigned to you. Open a task for the details."}
        </p>
      </header>
      {loading ? (
        <section className="card">
          <p className="muted">Loading…</p>
        </section>
      ) : tasks.length === 0 ? (
        <section className="card empty">
          <p>Nothing is assigned to you yet.</p>
          <p className="muted">A notification will show up here when it is.</p>
        </section>
      ) : (
        <ul className="task-list">
          {tasks.map((task) => {
            const mine = task.assignments?.find((item) => item.user_id === user?.id);
            return (
              <li key={task.id}>
                <Link to={`/tasks/${task.id}`} className="task-card-main">
                  <span className="task-card-head">
                    <strong>{task.title}</strong>
                    <span className={`badge badge-${task.status}`}>{statusLabel(task.status)}</span>
                  </span>
                  <span className="task-meta">
                    {task.project_name && <span>{task.project_name}</span>}
                    <span>{formatDate(task.due_at)}</span>
                  </span>
                  {mine && (
                    <span className="progress-field">
                      <span className="field-label">Your progress {mine.progress}%</span>
                      <ProgressBar value={mine.progress} />
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
