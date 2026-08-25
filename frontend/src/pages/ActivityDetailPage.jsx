import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Clock, Gauge, MapPinned } from "lucide-react";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import RouteMap from "../components/RouteMap.jsx";
import StatTile from "../components/StatTile.jsx";
import { formatDistanceKm, formatDuration, formatPace } from "../utils/format.js";

export default function ActivityDetailPage() {
  const { activityId } = useParams();
  const navigate = useNavigate();
  const [activity, setActivity] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .activity(activityId)
      .then((data) => setActivity(data.activity))
      .catch((err) => setError(err.message));
  }, [activityId]);

  async function deleteActivity() {
    await api.deleteActivity(activityId);
    navigate("/profile");
  }

  if (error) {
    return (
      <section className="page">
        <div className="empty-state">{error}</div>
        <Link className="button-link" to="/profile">Back to profile</Link>
      </section>
    );
  }

  if (!activity) return <section className="page">Loading...</section>;

  return (
    <section className="page">
      <PageHero eyebrow={`${activity.activity_type} - ${activity.source}`} title={formatDistanceKm(activity.distance_meters)}>
        <p>{new Date(activity.started_at).toLocaleString()}</p>
      </PageHero>
      <div className="metric-grid">
        <StatTile icon={Clock} value={formatDuration(activity.duration_seconds)} label="Duration" />
        <StatTile icon={Gauge} value={formatPace(activity.duration_seconds, activity.distance_meters)} label="Pace" />
        <StatTile icon={MapPinned} value={activity.route_points.length} label="GPS points" tone="accent" />
      </div>
      {activity.route_points.length ? (
        <RouteMap points={activity.route_points} />
      ) : (
        <div className="empty-state">No GPS route was saved for this activity.</div>
      )}
      <div className="action-row">
        <Link className="button-link" to="/profile">Back</Link>
        <button type="button" onClick={deleteActivity}>Delete activity</button>
      </div>
    </section>
  );
}
