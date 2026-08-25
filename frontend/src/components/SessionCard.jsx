import { Link } from "react-router-dom";

import { formatDistanceKm, formatSessionTime } from "../utils/format.js";

export default function SessionCard({ session }) {
  return (
    <Link className="card session-card" to={`/sessions/${session.id}`}>
      <div>
        <p className="eyebrow">{session.crew_name || "Group session"}</p>
        <h3>{session.title}</h3>
        <p>{formatSessionTime(session.scheduled_start)} at {session.meeting_point_name}</p>
      </div>
      <div className="card-meta">
        <span>{formatDistanceKm(session.expected_distance_m)}</span>
        <span>{session.difficulty || "open"}</span>
        <span>{session.attendee_count} going</span>
      </div>
    </Link>
  );
}

