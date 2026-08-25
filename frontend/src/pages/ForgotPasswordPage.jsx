import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    try {
      const response = await api.forgotPassword({ email });
      setMessage(response.message);
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <p className="eyebrow">Password recovery</p>
        <h1>Reset access</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          {message && <p className="empty-state">{message}</p>}
          <button type="submit">Send reset link</button>
        </form>
        <p>
          Remembered it? <Link to="/login">Log in</Link>
        </p>
      </section>
    </main>
  );
}
