import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { homePath } from "../lib/format";
import { notify } from "../lib/notify";

const SAMPLES = [
  { role: "Admin", email: "admin@taskmanager.local", password: "admin1234" },
  { role: "Project lead", email: "lead@taskmanager.local", password: "lead1234" },
  { role: "Member", email: "member@taskmanager.local", password: "member1234" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const me = await login(email, password);
      notify.success(`Welcome back${me.name ? `, ${me.name}` : ""}`);
      navigate(homePath(me.role));
    } catch (err) {
      notify.fromError(err, "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <aside className="auth-visual" aria-hidden="true">
        <div className="auth-visual-inner">
          <h1 className="auth-brand">
            Task<em>Manager</em>
          </h1>
          <p>Admins set up the work. Leads move it forward. Members see what is theirs.</p>
        </div>
      </aside>
      <div className="auth-panel">
        <form className="auth-card" onSubmit={handleSubmit}>
          <h1>Welcome back</h1>
          <p className="muted">Sign in. Your role decides what you can do next.</p>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
          <div className="sample-row">
            {SAMPLES.map((sample) => (
              <button
                key={sample.role}
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => {
                  setEmail(sample.email);
                  setPassword(sample.password);
                }}
              >
                {sample.role}
              </button>
            ))}
          </div>
          <p className="auth-footer">
            No account? <Link to="/register">Create one</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
