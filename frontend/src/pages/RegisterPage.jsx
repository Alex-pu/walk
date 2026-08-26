import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({ name: "", email: "", password: "", neighborhood: "" });
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      await register(form);
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
        <p className="eyebrow">Start nearby</p>
        <h1>Create your account</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Name
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </label>
          <label>
            Email
            <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          </label>
          <label>
            Password
            <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          </label>
          <label>
            Neighborhood
            <input value={form.neighborhood} onChange={(event) => setForm({ ...form, neighborhood: event.target.value })} />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit">Create account</button>
        </form>
        <p>
          Already registered? <Link to={`/login${searchParams.get("next") ? `?next=${encodeURIComponent(searchParams.get("next"))}` : ""}`}>Log in</Link>
        </p>
      </section>
    </main>
  );
}
