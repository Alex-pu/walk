import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Gauge, MapPinned, Users } from "lucide-react";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import StatTile from "../components/StatTile.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDistanceKm, formatSessionTime } from "../utils/format.js";

export default function SessionDetailPage() {
  const { user } = useAuth();
  const { sessionId } = useParams();
  const [session, setSession] = useState(null);
  const [message, setMessage] = useState("");

  function loadSession() {
    api.session(sessionId).then((data) => setSession(data.session));
  }

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  async function runAction(action, successMessage) {
    setMessage("");
    try {
      const data = await action();
      if (data.session) setSession(data.session);
      else loadSession();
      setMessage(successMessage);
    } catch (error) {
      setMessage(error.message);
    }
  }

  if (!session) return <section className="page">Loading...</section>;

  const attendance = session.current_user_attendance;
  const attendanceStatus = attendance?.status;
  const isOpen = ["scheduled", "active"].includes(session.status);

  return (
    <section className="page">
      <PageHero eyebrow={session.crew_name} title={session.title}>
        <p>{formatSessionTime(session.scheduled_start)} at {session.meeting_point_name}</p>
        <span className={`status-pill status-${session.status}`}>{session.status}</span>
      </PageHero>
      <div className="metric-grid">
        <StatTile icon={MapPinned} value={formatDistanceKm(session.expected_distance_m)} label="Distance" tone="accent" />
        <StatTile icon={Gauge} value={session.difficulty || "Open"} label="Difficulty" />
        <StatTile icon={Users} value={session.attendee_count} label="Going" />
      </div>
      <div className="action-row">
        {!attendanceStatus && isOpen && (
          <button onClick={() => runAction(() => api.joinSession(sessionId), "You're going.")}>Join</button>
        )}
        {attendanceStatus === "going" && isOpen && (
          <button onClick={() => runAction(() => api.checkIn(sessionId), "Checked in.")}>Check in</button>
        )}
        {attendanceStatus === "checked_in" && isOpen && (
          <>
            <Link className="button-link" to="/activity" state={{ session }}>Start activity</Link>
            <button onClick={() => runAction(() => api.checkOut(sessionId), "Checked out.")}>Check out</button>
          </>
        )}
        {attendanceStatus === "completed" && <span className="status-pill status-completed">Completed</span>}
        {attendanceStatus === "cancelled" && <span className="status-pill status-cancelled">Cancelled</span>}
        {attendanceStatus === "no_show" && <span className="status-pill status-no_show">No show</span>}
      </div>
      {session.can_manage_session && (
        <>
          <p className="section-label">Organizer controls</p>
          <div className="action-row">
            {session.status !== "cancelled" && session.status !== "completed" && (
              <button onClick={() => runAction(() => api.cancelSession(sessionId), "Session cancelled.")}>Cancel session</button>
            )}
            {session.status !== "completed" && session.status !== "cancelled" && (
              <button onClick={() => runAction(() => api.completeSession(sessionId), "Session completed.")}>Complete session</button>
            )}
          </div>
        </>
      )}
      {message && <p className="empty-state">{message}</p>}
      <p className="section-label">Attendees</p>
      <div className="stack">
        {session.attendees.map((attendee) => (
          <div className="card" key={attendee.id}>
            <div>
              <strong>{attendee.name}</strong>
              <p>{attendee.user_id === user.id ? "You" : "Participant"}</p>
            </div>
            <div className="compact-actions">
              <span className={`status-pill status-${attendee.status}`}>{attendee.status.replace("_", " ")}</span>
              {session.can_manage_session && attendee.status === "going" && (
                <button
                  type="button"
                  onClick={() => runAction(() => api.markNoShow(sessionId, attendee.user_id), "Marked no-show.")}
                >
                  No-show
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
