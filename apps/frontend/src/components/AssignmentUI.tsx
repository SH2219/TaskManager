import { roleLabel, roleRank } from "../lib/format";

type Person = {
  id: number;
  name?: string | null;
  email: string;
  role?: string | null;
};

export function UserMultiSelect({
  users,
  selectedIds,
  onChange,
  label,
  hint,
}: {
  users: Person[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
  label: string;
  hint?: string;
}) {
  function toggle(id: number) {
    if (selectedIds.includes(id)) onChange(selectedIds.filter((item) => item !== id));
    else onChange([...selectedIds, id]);
  }

  if (users.length === 0) {
    return <p className="muted">No people to choose from yet.</p>;
  }

  const ordered = [...users].sort((a, b) => {
    const rank = roleRank(a.role) - roleRank(b.role);
    if (rank !== 0) return rank;
    return (a.name || a.email).localeCompare(b.name || b.email);
  });
  const leads = ordered.filter((user) => user.role === "project_lead");
  const others = ordered.filter((user) => user.role !== "project_lead");

  function renderPerson(user: Person) {
    const checked = selectedIds.includes(user.id);
    return (
      <li key={user.id}>
        <label className={checked ? "person-chip selected" : "person-chip"}>
          <input type="checkbox" checked={checked} onChange={() => toggle(user.id)} />
          <span>
            <strong>{user.name || user.email}</strong>
            {user.role && <span className={`role-pill role-${user.role}`}>{roleLabel(user.role)}</span>}
            {user.name && <span className="muted">{user.email}</span>}
          </span>
        </label>
      </li>
    );
  }

  return (
    <fieldset className="people-select">
      <legend>{label}</legend>
      {hint && <p className="muted people-hint">{hint}</p>}
      {leads.length > 0 && (
        <div className="people-group">
          <p className="people-group-label">Project leads</p>
          <ul className="people-list">{leads.map(renderPerson)}</ul>
        </div>
      )}
      <div className="people-group">
        {leads.length > 0 && <p className="people-group-label">Everyone else</p>}
        <ul className="people-list">{(leads.length > 0 ? others : ordered).map(renderPerson)}</ul>
      </div>
    </fieldset>
  );
}

export function ProgressBar({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="progress" role="progressbar" aria-valuenow={clamped} aria-valuemin={0} aria-valuemax={100}>
      <span style={{ width: `${clamped}%` }} />
    </div>
  );
}

export function StarRating({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (rating: number) => void;
}) {
  return (
    <div className="stars" role="group" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={value != null && star <= value ? "star on" : "star"}
          aria-label={`${star} star${star === 1 ? "" : "s"}`}
          onClick={() => onChange(star)}
        >
          ★
        </button>
      ))}
    </div>
  );
}
