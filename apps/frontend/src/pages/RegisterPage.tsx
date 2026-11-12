import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { homePath } from "../lib/format";
import { notify } from "../lib/notify";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const me = await register({
        name: name.trim() || undefined,
        email: email.trim(),
        phone: phone.trim() || undefined,
        password,
      });
      notify.success("Account created. You’re signed in as a member.");
      navigate(homePath(me.role));
    } catch (err) {
      notify.fromError(err, "Could not create account");
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
          <p>Start a workspace, invite a team, and keep the work visible.</p>
        </div>
      </aside>
      <div className="auth-panel">
        <form className="auth-card" onSubmit={handleSubmit}>
          <h1>Create account</h1>
          <p className="muted">New accounts join as members. An admin can change that later.</p>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
          </label>
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
            Phone
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              autoComplete="tel"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Creating…" : "Create account"}
          </button>
          <p className="auth-footer">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
