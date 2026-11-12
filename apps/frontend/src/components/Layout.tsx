import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "../api";
import type { NotificationItem } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { homePath, roleLabel } from "../lib/format";
import { notify } from "../lib/notify";

function NavIcon({ label }: { label: string }) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (label === "Users") {
    return (
      <svg {...common}>
        <path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
        <circle cx="9.5" cy="7" r="3" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a3 3 0 0 1 0 5.75" />
      </svg>
    );
  }
  if (label === "Projects") {
    return (
      <svg {...common}>
        <path d="M3 7.5 12 3l9 4.5-9 4.5L3 7.5Z" />
        <path d="M3 12.5 12 17l9-4.5" />
        <path d="M3 17.5 12 22l9-4.5" />
      </svg>
    );
  }
  if (label === "My tasks") {
    return (
      <svg {...common}>
        <path d="M9 6h11" />
        <path d="M9 12h11" />
        <path d="M9 18h11" />
        <path d="M4 6h.01" />
        <path d="M4 12h.01" />
        <path d="M4 18h.01" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5Z" />
    </svg>
  );
}

function initial(name?: string | null, email?: string | null) {
  const source = (name || email || "?").trim();
  return source.charAt(0).toUpperCase();
}

type LinkItem = { to: string; label: string; end?: boolean };

function linksFor(role?: string | null): LinkItem[] {
  if (role === "admin") {
    return [
      { to: "/admin", label: "Home", end: true },
      { to: "/users", label: "Users" },
      { to: "/projects", label: "Projects" },
    ];
  }
  if (role === "project_lead") {
    return [
      { to: "/projects", label: "Projects", end: true },
      { to: "/my-tasks", label: "My tasks" },
    ];
  }
  return [{ to: "/my-tasks", label: "My tasks", end: true }];
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [notes, setNotes] = useState<NotificationItem[]>([]);
  const [open, setOpen] = useState(false);
  const links = linksFor(user?.role);
  const unread = notes.filter((note) => !note.read_at).length;

  useEffect(() => {
    let active = true;
    function load() {
      listNotifications()
        .then((rows) => {
          if (active) setNotes(rows);
        })
        .catch(() => {
          if (active) setNotes([]);
        });
    }
    load();
    window.addEventListener("focus", load);
    return () => {
      active = false;
      window.removeEventListener("focus", load);
    };
  }, []);

  async function openNote(note: NotificationItem) {
    try {
      const next = note.read_at ? note : await markNotificationRead(note.id);
      setNotes((prev) => prev.map((item) => (item.id === note.id ? next : item)));
      setOpen(false);
      if (note.task_id) navigate(`/tasks/${note.task_id}`);
    } catch (err) {
      notify.fromError(err, "Could not update notification");
    }
  }

  async function markAll() {
    try {
      setNotes(await markAllNotificationsRead());
    } catch (err) {
      notify.fromError(err, "Could not mark notifications read");
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-row">
          <NavLink className="brand" to={homePath(user?.role)}>
            Task<em>Manager</em>
          </NavLink>
          <nav className="nav nav-desktop" aria-label="Primary">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.end}>
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="topbar-actions">
            <div className="identity" title={`${user?.name || user?.email || ""} · ${roleLabel(user?.role)}`}>
              <span className={`avatar role-${user?.role || "member"}`} aria-hidden="true">
                {initial(user?.name, user?.email)}
              </span>
              <span className="identity-copy">
                <span className="identity-name">{user?.name || user?.email}</span>
                <span className={`role-pill role-${user?.role || "member"}`}>{roleLabel(user?.role)}</span>
              </span>
            </div>
            <button
              type="button"
              className="bell"
              aria-label={unread ? `Notifications, ${unread} unread` : "Notifications"}
              aria-expanded={open}
              onClick={() => setOpen((value) => !value)}
            >
            <span aria-hidden="true" className="bell-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M6 9a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9" strokeLinecap="round" />
                <path d="M10 20a2 2 0 0 0 4 0" strokeLinecap="round" />
              </svg>
            </span>
              {unread > 0 && <span className="bell-count">{unread}</span>}
            </button>
            <button type="button" className="btn btn-ghost btn-sm btn-logout" onClick={logout} aria-label="Log out">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                <path d="M10 7V5a1 1 0 0 1 1-1h8v16h-8a1 1 0 0 1-1-1v-2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M4 12h11" strokeLinecap="round" />
                <path d="m12 9 3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="logout-label">Log out</span>
            </button>
          </div>
        </div>
        {open && (
          <section className="notif-panel" aria-label="Notifications">
            <div className="notif-head">
              <strong>Notifications</strong>
              {unread > 0 && (
                <button type="button" className="btn btn-ghost btn-sm" onClick={markAll}>
                  Mark all read
                </button>
              )}
            </div>
            {notes.length === 0 ? (
              <p className="muted">Nothing new yet.</p>
            ) : (
              <ul className="notif-list">
                {notes.map((note) => (
                  <li key={note.id}>
                    <button
                      type="button"
                      className={note.read_at ? "notif-item" : "notif-item unread"}
                      onClick={() => openNote(note)}
                    >
                      <strong>{note.title}</strong>
                      <span>{note.body}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
      </header>
      <main className="main">
        <Outlet />
      </main>
      <nav className="bottom-nav" aria-label="Primary">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end}>
            <NavIcon label={link.label} />
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export function PrivateRoute() {
  const { isAuthenticated, ready } = useAuth();
  if (!ready) return <p className="muted boot">Loading…</p>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Layout />;
}

export function PublicRoute() {
  const { isAuthenticated, ready, user } = useAuth();
  if (!ready) return <p className="muted boot">Loading…</p>;
  if (isAuthenticated) return <Navigate to={homePath(user?.role)} replace />;
  return <Outlet />;
}
