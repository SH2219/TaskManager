import { type FormEvent, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import {
  archiveProject,
  createProject,
  deleteProject,
  getProjectDashboard,
  listProjects,
  restoreProject,
} from "../api";
import type { Project, ProjectDashboard } from "../api/types";
import { ProgressBar } from "../components/AssignmentUI";
import { useAuth } from "../context/AuthContext";

export default function ProjectsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const isLead = user?.role === "project_lead";
  const [projects, setProjects] = useState<Project[]>([]);
  const [dashboards, setDashboards] = useState<Record<number, ProjectDashboard>>({});
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  async function load(includeArchived = showArchived) {
    setLoading(true);
    setError("");
    try {
      const rows = await listProjects(isAdmin && includeArchived);
      setProjects(rows);
      if (isLead) {
        const boards = await Promise.all(rows.map((project) => getProjectDashboard(project.id)));
        setDashboards(Object.fromEntries(boards.map((board) => [board.project_id, board])));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (isAdmin || isLead) load(showArchived);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin, isLead, showArchived]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError("");
    try {
      await createProject({ name: name.trim(), description: description.trim() || undefined });
      setName("");
      setDescription("");
      await load(showArchived);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setCreating(false);
    }
  }

  async function handleArchive(project: Project) {
    setError("");
    try {
      if (project.archived) await restoreProject(project.id);
      else await archiveProject(project.id);
      await load(showArchived);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the project");
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this archived project and its tasks?")) return;
    setError("");
    try {
      await deleteProject(id);
      await load(showArchived);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete the project");
    }
  }

  if (!isAdmin && !isLead) return <Navigate to="/my-tasks" replace />;

  return (
    <div className="page">
      <header className="page-header">
        <h1>{isLead ? "Assigned projects" : "Projects"}</h1>
        <p className="muted">
          {isLead
            ? "Open a project to update progress, change status, and mark work completed."
            : "Create a project, then add the lead, the members, and the tasks."}
        </p>
      </header>
      {error && <div className="alert alert-error">{error}</div>}

      {isAdmin && (
        <section className="card">
          <h2>Create project</h2>
          <form className="form-stack" onSubmit={handleCreate}>
            <input
              placeholder="Project name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <input
              placeholder="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? "Creating…" : "Create"}
            </button>
          </form>
          <label className="check-line">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            Show archived projects
          </label>
        </section>
      )}

      <section className="stack">
        <h2>{isLead ? "Your projects" : "All projects"}</h2>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : projects.length === 0 ? (
          <div className="card empty">
            <p>{isLead ? "No projects are assigned to you yet." : "No projects yet."}</p>
          </div>
        ) : (
          <ul className="project-list">
            {projects.map((project) => {
              const board = dashboards[project.id];
              return (
                <li key={project.id} className="project-card">
                  <div className="list-item-main">
                    <div className="task-card-head">
                      <Link to={`/projects/${project.id}`} className="list-title">
                        {project.name}
                      </Link>
                      {project.archived && <span className="badge">Archived</span>}
                    </div>
                    {project.description && <p className="muted">{project.description}</p>}
                    {board && (
                      <div className="progress-field">
                        <span className="field-label">
                          {board.progress}% · {board.completed_count} of {board.task_count} done
                        </span>
                        <ProgressBar value={board.progress} />
                      </div>
                    )}
                  </div>
                  <div className="project-actions">
                    <Link to={`/projects/${project.id}`} className="btn btn-primary btn-sm">
                      Open
                    </Link>
                    {isAdmin && (
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => handleArchive(project)}>
                        {project.archived ? "Restore" : "Archive"}
                      </button>
                    )}
                    {isAdmin && project.archived && (
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => handleDelete(project.id)}>
                        Delete
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
