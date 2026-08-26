import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, MapPin, Users } from "lucide-react";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import SessionCard from "../components/SessionCard.jsx";
import StatTile from "../components/StatTile.jsx";
import SupportFooter from "../components/SupportFooter.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDistanceKm, formatSessionTime } from "../utils/format.js";

export default function HomePage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [message, setMessage] = useState("");

  function loadSessions() {
    const params = user?.latitude && user?.longitude
      ? { latitude: user.latitude, longitude: user.longitude, radius_km: 10 }
      : {};
    api.nearbySessions(params).then((data) => setSessions(data.sessions)).catch(() => setSessions([]));
  }

  useEffect(() => {
    loadSessions();
  }, [user?.latitude, user?.longitude]);

  const nextSession = sessions[0];
  const nextAttendance = nextSession?.current_user_attendance;
  const nextAttendanceStatus = nextAttendance?.status;
  const nextIsOpen = nextSession && ["scheduled", "active"].includes(nextSession.status);

  async function runNextAction(action, successMessage) {
    if (!nextSession) return;
    setMessage("");
    try {
      await action();
      setMessage(successMessage);
      loadSessions();
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="page">
      <PageHero eyebrow="Good morning" title={`${user?.neighborhood || "Nearby"} activity`}>
        {!user?.latitude || !user?.longitude ? (
          <p>Add an approximate location in Profile to sort nearby sessions.</p>
        ) : null}
        <Link className="button-link hero-inline-link" to="/about">About RunCommunity</Link>
      </PageHero>

      {nextSession ? (
        <section className="next-session-panel">
          <p className="section-label">Next session</p>
          <div className="next-session-content">
            <p className="eyebrow">{nextSession.crew_name}</p>
            <h2>{nextSession.title}</h2>
            <p>{formatSessionTime(nextSession.scheduled_start)} at {nextSession.meeting_point_name}</p>
            <div className="metric-grid">
              <StatTile icon={MapPin} value={formatDistanceKm(nextSession.expected_distance_m)} label="Distance" tone="accent" />
              <StatTile icon={CalendarDays} value={nextSession.difficulty || "open"} label="Level" />
              <StatTile icon={Users} value={nextSession.attendee_count} label="Going" />
            </div>
          </div>
          <div className="action-row">
            {!nextAttendanceStatus && nextIsOpen && (
              <button onClick={() => runNextAction(() => api.joinSession(nextSession.id), "You're going.")}>I'm joining</button>
            )}
            {nextAttendanceStatus === "going" && nextIsOpen && (
              <button onClick={() => runNextAction(() => api.checkIn(nextSession.id), "Checked in.")}>Check in</button>
            )}
            {nextAttendanceStatus === "checked_in" && nextIsOpen && (
              <Link className="button-link" to="/activity" state={{ session: nextSession }}>Start</Link>
            )}
            {nextAttendanceStatus === "completed" && <span className="status-pill status-completed">Completed</span>}
          </div>
          {message && <p className="empty-state">{message}</p>}
        </section>
      ) : (
        <div className="empty-state">No upcoming sessions yet.</div>
      )}

      <p className="section-label">Near you</p>
      <div className="stack">
        {sessions.slice(1, 4).map((session) => (
          <SessionCard key={session.id} session={session} />
        ))}
      </div>
      <SupportFooter />
    </section>
  );
}
