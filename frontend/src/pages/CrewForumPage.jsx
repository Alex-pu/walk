import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import ThreadCard from "../components/ThreadCard.jsx";

const initialForm = {
  title: "",
  body: "",
  category: "general",
};

export default function CrewForumPage() {
  const { crewId } = useParams();
  const [crew, setCrew] = useState(null);
  const [threads, setThreads] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState("");

  function loadForum() {
    api.crew(crewId).then((data) => setCrew(data.crew)).catch((error) => setMessage(error.message));
    api.crewForumThreads(crewId).then((data) => setThreads(data.threads)).catch((error) => setMessage(error.message));
  }

  useEffect(() => {
    loadForum();
  }, [crewId]);

  async function createThread(event) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createCrewForumThread(crewId, form);
      setForm(initialForm);
      loadForum();
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="page">
      <PageHero eyebrow="Crew forum" title={crew?.name || "Crew discussion"}>
        <p>Discuss route issues, session questions, and local updates with this crew.</p>
      </PageHero>

      <Link className="button-link" to={`/crews/${crewId}`}>Back to crew</Link>

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
          placeholder="Start a crew discussion"
          value={form.body}
          onChange={(event) => setForm({ ...form, body: event.target.value })}
          required
        />
        {message && <p className="empty-state">{message}</p>}
        <button type="submit">Post to crew</button>
      </form>

      <p className="section-label">Crew threads</p>
      <div className="stack">
        {threads.map((thread) => (
          <ThreadCard key={thread.id} thread={thread} />
        ))}
        {!threads.length && <div className="empty-state">No crew threads yet.</div>}
      </div>
    </section>
  );
}
