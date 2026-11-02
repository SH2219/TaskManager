import { roleLabel } from "../lib/format";

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
}: {
  users: Person[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
  label: string;
}) {
  function toggle(id: number) {
    if (selectedIds.includes(id)) onChange(selectedIds.filter((item) => item !== id));
    else onChange([...selectedIds, id]);
  }

  if (users.length === 0) {
    return <p className="muted">No people to choose from yet.</p>;
  }

  return (
    <fieldset className="people-select">
      <legend>{label}</legend>
      <ul className="people-list">
        {users.map((user) => {
          const checked = selectedIds.includes(user.id);
          return (
            <li key={user.id}>
              <label className={checked ? "person-chip selected" : "person-chip"}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(user.id)}
                />
                <span>
                  <strong>{user.name || user.email}</strong>
                  {user.role && <span className="user-chip-role">{roleLabel(user.role)}</span>}
                  {user.name && <span className="muted">{user.email}</span>}
                </span>
              </label>
            </li>
          );
        })}
      </ul>
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
