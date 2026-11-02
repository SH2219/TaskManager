import { type FormEvent, useEffect, useState } from "react";
import { createUser, deleteUser, listUsers, updateUser } from "../api";
import type { User } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { roleLabel } from "../lib/format";

const ROLES = [
  { value: "admin", label: "Admin" },
  { value: "project_lead", label: "Project lead" },
  { value: "member", label: "Member" },
];

export default function UsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("member");
  const [creating, setCreating] = useState(false);
  const [drafts, setDrafts] = useState<Record<number, User>>({});
  const [savingId, setSavingId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const rows = await listUsers();
      setUsers(rows);
      setDrafts(Object.fromEntries(rows.map((row) => [row.id, row])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function patchDraft(id: number, patch: Partial<User>) {
    setDrafts((prev) => ({ ...prev, [id]: { ...prev[id], ...patch } }));
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setError("");
    try {
      await createUser({
        name: name.trim() || undefined,
        email: email.trim(),
        phone: phone.trim() || undefined,
        password,
        role,
      });
      setName("");
      setEmail("");
      setPhone("");
      setPassword("");
      setRole("member");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create user");
    } finally {
      setCreating(false);
    }
  }

  async function handleSave(id: number) {
    const draft = drafts[id];
    if (!draft?.email.trim()) return;
    setSavingId(id);
    setError("");
    try {
      await updateUser(id, {
        name: draft.name,
        email: draft.email.trim(),
        phone: draft.phone || null,
        role: draft.role || "member",
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update user");
    } finally {
      setSavingId(null);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this user?")) return;
    setError("");
    try {
      await deleteUser(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete user");
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>Users</h1>
        <p className="muted">Add people and set who is an admin, a project lead, or a member.</p>
      </header>
      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        <h2>Add user</h2>
        <form className="form-stack" onSubmit={handleCreate}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label>
            Email
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label>
            Phone
            <input value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <label>
            Role
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="btn btn-primary" disabled={creating}>
            {creating ? "Adding…" : "Add user"}
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Everyone</h2>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : (
          <ul className="list">
            {users.map((person) => {
              const draft = drafts[person.id] ?? person;
              return (
                <li key={person.id} className="list-item">
                  <div className="form-stack">
                    <div className="row-between">
                      <span className={`role-pill role-${draft.role || "member"}`}>
                        {roleLabel(draft.role)}
                      </span>
                      {person.id === me?.id && <span className="muted">You</span>}
                    </div>
                    <label>
                      Name
                      <input
                        value={draft.name ?? ""}
                        onChange={(e) => patchDraft(person.id, { name: e.target.value })}
                      />
                    </label>
                    <label>
                      Email
                      <input
                        type="email"
                        required
                        value={draft.email}
                        onChange={(e) => patchDraft(person.id, { email: e.target.value })}
                      />
                    </label>
                    <label>
                      Phone
                      <input
                        value={draft.phone ?? ""}
                        onChange={(e) => patchDraft(person.id, { phone: e.target.value })}
                      />
                    </label>
                    <label>
                      Role
                      <select
                        value={draft.role || "member"}
                        onChange={(e) => patchDraft(person.id, { role: e.target.value })}
                      >
                        {ROLES.map((item) => (
                          <option key={item.value} value={item.value}>
                            {item.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="form-row">
                      <button
                        type="button"
                        className="btn btn-primary"
                        disabled={savingId === person.id}
                        onClick={() => handleSave(person.id)}
                      >
                        {savingId === person.id ? "Saving…" : "Save"}
                      </button>
                      {person.id !== me?.id && (
                        <button type="button" className="btn btn-danger" onClick={() => handleDelete(person.id)}>
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
    </div>
  );
}
