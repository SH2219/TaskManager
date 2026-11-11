import { type FormEvent, useEffect, useMemo, useState } from "react";
import { createUser, deleteUser, listUsers, updateUser } from "../api";
import type { User } from "../api/types";
import { Sheet } from "../components/Sheet";
import { useAuth } from "../context/AuthContext";
import { roleHelp, roleLabel, roleRank } from "../lib/format";

const ROLES = [
  { value: "admin", label: "Admin" },
  { value: "project_lead", label: "Project lead" },
  { value: "member", label: "Member" },
] as const;

type RoleFilter = "all" | "admin" | "project_lead" | "member";

const emptyCreate = {
  name: "",
  email: "",
  phone: "",
  password: "",
  role: "member",
};

export default function UsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<RoleFilter>("all");
  const [query, setQuery] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState(emptyCreate);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [saving, setSaving] = useState(false);
  const [roleBusyId, setRoleBusyId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setUsers(await listUsers());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const counts = useMemo(
    () => ({
      all: users.length,
      admin: users.filter((person) => person.role === "admin").length,
      project_lead: users.filter((person) => person.role === "project_lead").length,
      member: users.filter((person) => (person.role || "member") === "member").length,
    }),
    [users],
  );

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return users
      .filter((person) => {
        const role = person.role || "member";
        if (filter !== "all" && role !== filter) return false;
        if (!needle) return true;
        const hay = `${person.name ?? ""} ${person.email} ${person.phone ?? ""}`.toLowerCase();
        return hay.includes(needle);
      })
      .sort((a, b) => {
        const rank = roleRank(a.role) - roleRank(b.role);
        if (rank !== 0) return rank;
        return (a.name || a.email).localeCompare(b.name || b.email);
      });
  }, [users, filter, query]);

  function closeCreate() {
    setShowCreate(false);
    setCreateForm(emptyCreate);
  }

  function openEdit(person: User) {
    setEditing({ ...person });
  }

  function closeEdit() {
    setEditing(null);
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setError("");
    setNotice("");
    try {
      await createUser({
        name: createForm.name.trim() || undefined,
        email: createForm.email.trim(),
        phone: createForm.phone.trim() || undefined,
        password: createForm.password,
        role: createForm.role,
      });
      closeCreate();
      setNotice(`${roleLabel(createForm.role)} added.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create user");
    } finally {
      setCreating(false);
    }
  }

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    if (!editing?.email.trim()) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      await updateUser(editing.id, {
        name: editing.name,
        email: editing.email.trim(),
        phone: editing.phone || null,
        role: editing.role || "member",
      });
      closeEdit();
      setNotice("User updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update user");
    } finally {
      setSaving(false);
    }
  }

  async function handleRoleChange(person: User, role: string) {
    if ((person.role || "member") === role) return;
    if (person.id === me?.id && role !== "admin") {
      setError("You can’t remove your own admin role here.");
      return;
    }
    setRoleBusyId(person.id);
    setError("");
    setNotice("");
    try {
      await updateUser(person.id, { role });
      setNotice(`${person.name?.trim() || person.email} is now ${roleLabel(role)}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change role");
    } finally {
      setRoleBusyId(null);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this user?")) return;
    setError("");
    setNotice("");
    try {
      await deleteUser(id);
      if (editing?.id === id) closeEdit();
      setNotice("User deleted.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete user");
    }
  }

  const filters: { id: RoleFilter; label: string; count: number }[] = [
    { id: "all", label: "Everyone", count: counts.all },
    { id: "admin", label: "Admins", count: counts.admin },
    { id: "project_lead", label: "Leads", count: counts.project_lead },
    { id: "member", label: "Members", count: counts.member },
  ];

  return (
    <div className="page">
      <header className="page-header">
        <div className="row-between">
          <div>
            <h1>Users</h1>
            <p className="muted">
              Decide who runs the workspace, who leads projects, and who only receives assigned work.
            </p>
          </div>
          <button type="button" className="btn btn-primary" onClick={() => setShowCreate(true)}>
            Add user
          </button>
        </div>
      </header>
      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-ok">{notice}</div>}

      <section className="role-guide">
        {ROLES.map((item) => (
          <button
            key={item.value}
            type="button"
            className={`role-guide-card${filter === item.value ? " is-active" : ""}`}
            onClick={() => setFilter(item.value)}
          >
            <span className={`role-pill role-${item.value}`}>{item.label}</span>
            <strong>{counts[item.value]}</strong>
            <span className="muted">{roleHelp(item.value)}</span>
          </button>
        ))}
      </section>

      <section className="card">
        <div className="row-between">
          <h2>People</h2>
          <input
            className="search-input"
            placeholder="Search name or email"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search users"
          />
        </div>
        <div className="filter-row" role="tablist" aria-label="Filter by role">
          {filters.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={filter === item.id}
              className={`filter-chip${filter === item.id ? " is-active" : ""}`}
              onClick={() => setFilter(item.id)}
            >
              {item.label} ({item.count})
            </button>
          ))}
        </div>

        {loading ? (
          <p className="muted">Loading…</p>
        ) : visible.length === 0 ? (
          <p className="muted">No people match this view. Add a user or clear the filter.</p>
        ) : (
          <ul className="list">
            {visible.map((person) => {
              const role = person.role || "member";
              const busy = roleBusyId === person.id;
              return (
                <li key={person.id} className="list-item user-row">
                  <div className="list-item-main">
                    <p className="list-title">{person.name?.trim() || person.email}</p>
                    <p className="muted">{person.email}</p>
                    <div className="meta-row">
                      <span className={`role-pill role-${role}`}>{roleLabel(role)}</span>
                      {person.id === me?.id && <span className="muted">You</span>}
                    </div>
                    <p className="muted user-role-hint">{roleHelp(role)}</p>
                  </div>
                  <div className="user-row-actions">
                    <div className="project-actions">
                      {role !== "project_lead" && (
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          disabled={busy}
                          onClick={() => handleRoleChange(person, "project_lead")}
                        >
                          Make lead
                        </button>
                      )}
                      {role !== "member" && person.id !== me?.id && (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          disabled={busy}
                          onClick={() => handleRoleChange(person, "member")}
                        >
                          Make member
                        </button>
                      )}
                      {role !== "admin" && (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          disabled={busy}
                          onClick={() => handleRoleChange(person, "admin")}
                        >
                          Make admin
                        </button>
                      )}
                    </div>
                    <div className="project-actions">
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => openEdit(person)}>
                        Edit details
                      </button>
                      {person.id !== me?.id && (
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(person.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {showCreate && (
        <Sheet title="Add user" onClose={closeCreate}>
          <form className="form-stack" onSubmit={handleCreate}>
            <label>
              Name
              <input
                value={createForm.name}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, name: e.target.value }))}
              />
            </label>
            <label>
              Email
              <input
                type="email"
                required
                value={createForm.email}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, email: e.target.value }))}
              />
            </label>
            <label>
              Phone
              <input
                value={createForm.phone}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, phone: e.target.value }))}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                required
                minLength={6}
                value={createForm.password}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, password: e.target.value }))}
              />
            </label>
            <fieldset className="role-pick">
              <legend>Role</legend>
              <p className="muted">Pick what this person can do after they sign in.</p>
              <div className="role-pick-list">
                {ROLES.map((item) => (
                  <label key={item.value} className={`role-pick-option${createForm.role === item.value ? " is-active" : ""}`}>
                    <input
                      type="radio"
                      name="create-role"
                      value={item.value}
                      checked={createForm.role === item.value}
                      onChange={() => setCreateForm((prev) => ({ ...prev, role: item.value }))}
                    />
                    <span>
                      <strong>{item.label}</strong>
                      <span className="muted">{roleHelp(item.value)}</span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? "Adding…" : "Add user"}
            </button>
          </form>
        </Sheet>
      )}

      {editing && (
        <Sheet title="Edit user" onClose={closeEdit}>
          <form className="form-stack" onSubmit={handleSave}>
            <label>
              Name
              <input
                value={editing.name ?? ""}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })}
              />
            </label>
            <label>
              Email
              <input
                type="email"
                required
                value={editing.email}
                onChange={(e) => setEditing({ ...editing, email: e.target.value })}
              />
            </label>
            <label>
              Phone
              <input
                value={editing.phone ?? ""}
                onChange={(e) => setEditing({ ...editing, phone: e.target.value })}
              />
            </label>
            <fieldset className="role-pick">
              <legend>Role</legend>
              <div className="role-pick-list">
                {ROLES.map((item) => (
                  <label
                    key={item.value}
                    className={`role-pick-option${(editing.role || "member") === item.value ? " is-active" : ""}`}
                  >
                    <input
                      type="radio"
                      name="edit-role"
                      value={item.value}
                      checked={(editing.role || "member") === item.value}
                      disabled={editing.id === me?.id && item.value !== "admin"}
                      onChange={() => setEditing({ ...editing, role: item.value })}
                    />
                    <span>
                      <strong>{item.label}</strong>
                      <span className="muted">{roleHelp(item.value)}</span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="form-row">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </button>
              {editing.id !== me?.id && (
                <button type="button" className="btn btn-danger" onClick={() => handleDelete(editing.id)}>
                  Delete
                </button>
              )}
            </div>
          </form>
        </Sheet>
      )}
    </div>
  );
}
