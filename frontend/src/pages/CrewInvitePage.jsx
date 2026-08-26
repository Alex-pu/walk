import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function CrewInvitePage() {
  const { crewId } = useParams();
  const navigate = useNavigate();
  const { user, loading } = useAuth();
  const [message, setMessage] = useState("Preparing your crew invite...");

  useEffect(() => {
    if (loading) return;

    if (!user) {
      const invitePath = `/join/crew/${crewId}`;
      window.localStorage.setItem("runcommunity_pending_invite", invitePath);
      setMessage("Create an account or log in to join this crew.");
      return;
    }

    api
      .joinCrew(crewId)
      .then(() => navigate(`/crews/${crewId}`, { replace: true }))
      .catch((error) => setMessage(error.message));
  }, [crewId, loading, navigate, user]);

  return (
    <section className="page">
      <PageHero eyebrow="Crew invite" title="Join this crew">
        <p>{message}</p>
      </PageHero>
      {!user && !loading && (
        <div className="action-row">
          <Link className="button-link" to={`/register?next=/join/crew/${crewId}`}>Create account</Link>
          <Link className="button-link" to={`/login?next=/join/crew/${crewId}`}>Log in</Link>
        </div>
      )}
    </section>
  );
}
