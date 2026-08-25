import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { Gauge, MapPinned } from "lucide-react";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import RouteMap from "../components/RouteMap.jsx";
import StatTile from "../components/StatTile.jsx";
import {
  clearActiveActivity,
  clearActivityContext,
  loadActivityContext,
  loadPendingActivities,
  removePendingActivity,
  saveActivityContext,
  savePendingActivity,
} from "../tracking/activityStorage.js";
import { createActivityTimer } from "../tracking/activityTimer.js";
import { createGpsTracker } from "../tracking/gpsTracker.js";
import { formatDuration, formatPace } from "../utils/format.js";

export default function ActivityPage() {
  const location = useLocation();
  const [activityContext, setActivityContext] = useState(() => {
    const routedSession = location.state?.session;
    return routedSession ? { session: routedSession } : loadActivityContext();
  });
  const session = activityContext?.session || null;
  const timerRef = useRef(createActivityTimer());
  const trackerRef = useRef(null);
  const intervalRef = useRef(null);
  const [seconds, setSeconds] = useState(0);
  const [meters, setMeters] = useState(0);
  const [route, setRoute] = useState([]);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const [pendingCount, setPendingCount] = useState(0);
  const [mode, setMode] = useState("gps");
  const [manualForm, setManualForm] = useState({
    activity_type: session?.activity_type || "walk",
    distance_km: "",
    duration_minutes: "",
    started_at: new Date().toISOString().slice(0, 16),
  });

  useEffect(() => {
    trackerRef.current = createGpsTracker({
      getTimerSnapshot: () => timerRef.current.getSnapshot(),
      onUpdate: (snapshot) => {
        setStatus(snapshot.status);
        setMeters(snapshot.totalMeters);
        setRoute(snapshot.route);
      },
    });

    trackerRef.current.restore().then((saved) => {
      if (saved?.timer) {
        timerRef.current.start(saved.timer);
        startTicker();
      }
    });
    loadPendingActivities().then((pending) => setPendingCount(pending.length));

    return () => window.clearInterval(intervalRef.current);
  }, []);

  function startTicker() {
    window.clearInterval(intervalRef.current);
    intervalRef.current = window.setInterval(() => {
      setSeconds(timerRef.current.getDurationSeconds());
    }, 1000);
  }

  function startActivity() {
    setMessage("");
    if (session) {
      const context = { session };
      saveActivityContext(context);
      setActivityContext(context);
    }
    timerRef.current.start();
    trackerRef.current.start();
    setStatus("active");
    startTicker();
  }

  function pauseActivity() {
    timerRef.current.pause();
    trackerRef.current.pause();
    setStatus("paused");
  }

  function resumeActivity() {
    timerRef.current.resume();
    trackerRef.current.resume();
    setStatus("active");
  }

  async function finishActivity() {
    const finished = trackerRef.current.finish();
    const duration = timerRef.current.getDurationSeconds();
    window.clearInterval(intervalRef.current);
    setStatus("finished");

    const payload = {
      local_id: crypto.randomUUID(),
      session_id: session?.id,
      activity_type: session?.activity_type || "walk",
      started_at: new Date(finished.started_at || Date.now()).toISOString(),
      finished_at: new Date().toISOString(),
      duration_seconds: duration,
      distance_meters: finished.distance_meters,
      source: "web_gps",
      route_points: finished.route,
    };

    try {
      await api.createActivity(payload);
      await clearActiveActivity();
      clearActivityContext();
      setMessage("Activity saved.");
    } catch (error) {
      await savePendingActivity(payload);
      clearActivityContext();
      const pending = await loadPendingActivities();
      setPendingCount(pending.length);
      setMessage("Activity saved locally and will need sync.");
    }
  }

  async function syncPending() {
    const pending = await loadPendingActivities();
    for (const activity of pending) {
      await api.createActivity(activity);
      await removePendingActivity(activity.local_id);
    }
    const remaining = await loadPendingActivities();
    setPendingCount(remaining.length);
    setMessage("Pending activities synced.");
  }

  async function saveManualActivity(event) {
    event.preventDefault();
    setMessage("");
    const durationSeconds = Math.round(Number(manualForm.duration_minutes) * 60);
    const distanceMeters = Math.round(Number(manualForm.distance_km) * 1000);
    const startedAt = new Date(manualForm.started_at);
    const finishedAt = new Date(startedAt.getTime() + durationSeconds * 1000);

    const payload = {
      local_id: crypto.randomUUID(),
      session_id: session?.id,
      activity_type: manualForm.activity_type,
      started_at: startedAt.toISOString(),
      finished_at: finishedAt.toISOString(),
      duration_seconds: durationSeconds,
      distance_meters: distanceMeters,
      source: "manual",
      route_points: [],
    };

    try {
      await api.createActivity(payload);
      setManualForm((current) => ({ ...current, distance_km: "", duration_minutes: "" }));
      setMessage("Manual activity saved.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  function updateManualForm(field, value) {
    setManualForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <section className="activity-screen">
      <PageHero eyebrow="Activity" title={session?.title || "Morning Walk"}>
        {session && <p>{session.crew_name} at {session.meeting_point_name}</p>}
      </PageHero>
      <div className="segmented-control">
        <button className={mode === "gps" ? "active-filter" : ""} onClick={() => setMode("gps")}>GPS</button>
        <button className={mode === "manual" ? "active-filter" : ""} onClick={() => setMode("manual")}>Manual</button>
      </div>
      {mode === "manual" ? (
        <form className="compact-form" onSubmit={saveManualActivity}>
          <div className="form-grid">
            <select value={manualForm.activity_type} onChange={(event) => updateManualForm("activity_type", event.target.value)}>
              <option value="walk">Walk</option>
              <option value="run">Run</option>
              <option value="mixed">Mixed</option>
            </select>
            <input
              type="datetime-local"
              value={manualForm.started_at}
              onChange={(event) => updateManualForm("started_at", event.target.value)}
              required
            />
          </div>
          <div className="form-grid">
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="Distance km"
              value={manualForm.distance_km}
              onChange={(event) => updateManualForm("distance_km", event.target.value)}
              required
            />
            <input
              type="number"
              min="1"
              step="1"
              placeholder="Duration minutes"
              value={manualForm.duration_minutes}
              onChange={(event) => updateManualForm("duration_minutes", event.target.value)}
              required
            />
          </div>
          <button type="submit">Save manual activity</button>
        </form>
      ) : (
        <>
      <p className="gps-status">GPS status: {status}</p>
      <div className="live-metric">{formatDuration(seconds)}</div>
      <div className="activity-stats">
        <StatTile icon={MapPinned} value={`${(meters / 1000).toFixed(2)} km`} label="Distance" tone="accent" />
        <StatTile icon={Gauge} value={formatPace(seconds, meters)} label="Average pace" />
      </div>
      <RouteMap points={route} />
      <p className="gps-status">{route.length} GPS points recorded</p>
      <div className="action-row">
        {status === "idle" || status === "finished" ? <button onClick={startActivity}>Start</button> : null}
        {status === "active" ? <button onClick={pauseActivity}>Pause</button> : null}
        {status === "paused" ? <button onClick={resumeActivity}>Resume</button> : null}
        {status === "active" || status === "paused" ? <button onClick={finishActivity}>Finish</button> : null}
      </div>
        </>
      )}
      {pendingCount > 0 && <button onClick={syncPending}>Sync {pendingCount} pending</button>}
      {message && <p className="empty-state">{message}</p>}
    </section>
  );
}
