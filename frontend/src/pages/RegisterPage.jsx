import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", neighborhood: "" });
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      await register(form);
      navigate("/home");
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
          Already registered? <Link to="/login">Log in</Link>
        </p>
      </section>
    </main>
  );
}
