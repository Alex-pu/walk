import { useEffect, useState } from "react";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import ThreadCard from "../components/ThreadCard.jsx";

const initialForm = {
  title: "",
  body: "",
  category: "general",
};

export default function ForumPage() {
  const [threads, setThreads] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState("");

  function loadThreads() {
    api.forumThreads().then((data) => setThreads(data.threads)).catch((error) => setMessage(error.message));
  }

  useEffect(() => {
    loadThreads();
  }, []);

  async function createThread(event) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createForumThread(form);
      setForm(initialForm);
      loadThreads();
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="page">
      <PageHero eyebrow="Forum" title="Community issues">
        <p>Raise app-wide questions, issues, requests, and announcements.</p>
      </PageHero>

      <form className="compact-form" onSubmit={createThread}>
        <input
          placeholder="Thread title"
          value={form.title}
          onChange={(event) => setForm({ ...form, title: event.target.value })}
          required
        />
        <select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>
          <option value="general">General</option>
          <option value="issue">Issue</option>
          <option value="question">Question</option>
          <option value="announcement">Announcement</option>
        </select>
        <textarea
          placeholder="What should the community know?"
          value={form.body}
          onChange={(event) => setForm({ ...form, body: event.target.value })}
          required
        />
        {message && <p className="empty-state">{message}</p>}
        <button type="submit">Post thread</button>
      </form>

      <p className="section-label">Latest threads</p>
      <div className="stack">
        {threads.map((thread) => (
          <ThreadCard key={thread.id} thread={thread} />
        ))}
        {!threads.length && <div className="empty-state">No community threads yet.</div>}
      </div>
    </section>
  );
}
