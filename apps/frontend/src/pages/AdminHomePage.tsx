import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listProjects, listTasks, listUsers } from "../api";
import { DashboardPanel } from "../components/Dashboard";

export default function AdminHomePage() {
  const [counts, setCounts] = useState({ users: 0, projects: 0, tasks: 0, done: 0 });
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([listUsers(), listProjects(true), listTasks()])
      .then(([users, projects, tasks]) => {
        setCounts({
          users: users.length,
          projects: projects.length,
          tasks: tasks.length,
          done: tasks.filter((task) => task.status === "done").length,
        });
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load the workspace"));
  }, []);

  const progress = counts.tasks ? Math.round((counts.done / counts.tasks) * 100) : 0;

  return (
    <div className="page">
      {error && <div className="alert alert-error">{error}</div>}
      <DashboardPanel
        eyebrow="Admin"
        title="Workspace"
        note="People, projects, and the tasks moving through them."
        progress={progress}
        progressLabel="tasks done"
        stats={[
          { label: "People", value: counts.users, to: "/users" },
          { label: "Projects", value: counts.projects, to: "/projects" },
          { label: "Open tasks", value: Math.max(counts.tasks - counts.done, 0) },
        ]}
      />
      <section className="card">
        <h2>Start here</h2>
        <div className="action-grid">
          <Link className="action-tile" to="/users">
            <strong>Manage users</strong>
            <span>Edit roles, or add and remove people.</span>
          </Link>
          <Link className="action-tile" to="/projects">
            <strong>Projects</strong>
            <span>Create work, add a team, or archive it.</span>
          </Link>
          <Link className="action-tile" to="/tags">
            <strong>Tags</strong>
            <span>Keep labels consistent across tasks.</span>
          </Link>
        </div>
      </section>
    </div>
  );
}
