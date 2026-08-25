import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/client.js";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const token = searchParams.get("token") || "";

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    try {
      const response = await api.resetPassword({ token, password });
      setMessage(response.message);
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <p className="eyebrow">Password recovery</p>
        <h1>New password</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          {message && <p className="empty-state">{message}</p>}
          <button type="submit" disabled={!token}>Update password</button>
        </form>
        <p>
          Done? <Link to="/login">Log in</Link>
        </p>
      </section>
    </main>
  );
}
