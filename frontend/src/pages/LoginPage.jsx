import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      await login(form);
      const next = searchParams.get("next") || window.localStorage.getItem("runcommunity_pending_invite") || "/home";
      window.localStorage.removeItem("runcommunity_pending_invite");
      navigate(next);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <p className="eyebrow">Run Community Kenya</p>
        <h1>Welcome back</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          </label>
          <label>
            Password
            <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit">Log in</button>
        </form>
        <p>
          New here? <Link to={`/register${searchParams.get("next") ? `?next=${encodeURIComponent(searchParams.get("next"))}` : ""}`}>Create an account</Link>
        </p>
        <p>
          Forgot password? <Link to="/forgot-password">Send reset link</Link>
        </p>
      </section>
    </main>
  );
}
