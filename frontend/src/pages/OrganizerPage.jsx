import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";

export default function OrganizerPage() {
  const [crews, setCrews] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api
      .crews()
      .then((data) => {
        setCrews(data.crews.filter((crew) => crew.current_user_role === "organizer"));
      })
      .catch((error) => setMessage(error.message));
  }, []);

  return (
    <section className="page">
      <PageHero eyebrow="Organizer" title="Manage your crews">
        <p>Open a crew to create sessions, review reports, and manage day-to-day activity.</p>
      </PageHero>

      {message && <p className="empty-state">{message}</p>}

      <div className="stack">
        {crews.map((crew) => (
          <Link className="admin-row" to={`/crews/${crew.id}`} key={crew.id}>
            <div>
              <strong>{crew.name}</strong>
              <p>{crew.meeting_point_name}</p>
              <p>{crew.activity_type} - {crew.member_count} members</p>
            </div>
            <span className="status-pill status-active">Organizer</span>
            <span className="button-link">Manage</span>
          </Link>
        ))}
        {!crews.length && !message && (
          <div className="empty-state">You are not an organizer for any crews yet.</div>
        )}
      </div>
    </section>
  );
}
