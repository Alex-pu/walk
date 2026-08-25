import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Clock, Gauge, MapPinned, Trophy, Users, Zap } from "lucide-react";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import PlacePicker from "../components/PlacePicker.jsx";
import StatTile from "../components/StatTile.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useInstallPrompt } from "../hooks/useInstallPrompt.js";
import { loadPendingActivities, removePendingActivity } from "../tracking/activityStorage.js";
import { formatDistanceKm, formatDuration, formatPaceFromSeconds } from "../utils/format.js";

export default function ProfilePage() {
  const { user, logout, updateProfile } = useAuth();
  const [activities, setActivities] = useState([]);
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [profileForm, setProfileForm] = useState({
    name: user.name || "",
    phone: user.phone || "",
    neighborhood: user.neighborhood || "",
    latitude: user.latitude ?? "",
    longitude: user.longitude ?? "",
  });
  const [profileMessage, setProfileMessage] = useState("");
  const { canInstall, isInstalled, install } = useInstallPrompt();

  async function loadProfile() {
    api.activities().then((data) => setActivities(data.activities)).catch(() => setActivities([]));
    api.activityStats().then((data) => setStats(data)).catch(() => setStats(null));
    setPending(await loadPendingActivities());
  }

  useEffect(() => {
    loadProfile();
  }, []);

  async function syncPending() {
    for (const activity of pending) {
      await api.createActivity(activity);
      await removePendingActivity(activity.local_id);
    }
    loadProfile();
  }

  async function deleteActivity(activityId) {
    await api.deleteActivity(activityId);
    loadProfile();
  }

  async function saveProfile(event) {
    event.preventDefault();
    setProfileMessage("");
    try {
      const updated = await updateProfile(profileForm);
      setProfileForm({
        name: updated.name || "",
        phone: updated.phone || "",
        neighborhood: updated.neighborhood || "",
        latitude: updated.latitude ?? "",
        longitude: updated.longitude ?? "",
      });
      setProfileMessage("Profile updated.");
    } catch (error) {
      setProfileMessage(error.message);
    }
  }

  function useApproximateLocation() {
    setProfileMessage("");
    if (!navigator.geolocation) {
      setProfileMessage("Location is not available in this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setProfileForm((current) => ({
          ...current,
          latitude: Number(position.coords.latitude.toFixed(5)),
          longitude: Number(position.coords.longitude.toFixed(5)),
        }));
        setProfileMessage("Approximate coordinates filled. Save to use them for discovery.");
      },
      () => setProfileMessage("Location permission was not granted."),
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 60000 }
    );
  }

  function updateField(field, value) {
    setProfileForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <section className="page">
      <PageHero eyebrow="Profile" title={`Hello, ${user.name}`}>
        <p>{user.neighborhood || "Set your neighborhood"}</p>
      </PageHero>
      <div className="metric-grid">
        <StatTile icon={MapPinned} value={formatDistanceKm(stats?.week.distance_meters || 0)} label="This week" tone="accent" />
        <StatTile icon={Users} value={stats?.week.sessions_attended || 0} label="Sessions" />
        <StatTile icon={Clock} value={formatDuration(stats?.week.duration_seconds || 0)} label="Week time" />
      </div>
      <div className="metric-grid">
        <StatTile icon={Zap} value={formatDistanceKm(stats?.month.distance_meters || 0)} label="This month" />
        <StatTile icon={Trophy} value={formatDistanceKm(stats?.best.longest_distance_meters || 0)} label="Longest" />
        <StatTile icon={Gauge} value={formatPaceFromSeconds(stats?.best.fastest_pace_seconds_per_km)} label="Best pace" />
      </div>
      <p className="section-label">Neighborhood setup</p>
      <form className="compact-form" onSubmit={saveProfile}>
        <input value={profileForm.name} onChange={(event) => updateField("name", event.target.value)} placeholder="Name" />
        <input value={profileForm.phone} onChange={(event) => updateField("phone", event.target.value)} placeholder="Phone optional" />
        <PlacePicker
          label="Neighborhood or landmark"
          value={profileForm.neighborhood}
          onChange={(place) =>
            setProfileForm((current) => ({
              ...current,
              neighborhood: place.name,
              latitude: place.latitude ?? current.latitude,
              longitude: place.longitude ?? current.longitude,
            }))
          }
        />
        {profileForm.latitude && profileForm.longitude && (
          <p className="field-hint">Selected location saved for nearby discovery.</p>
        )}
        <div className="action-row">
          <button type="button" onClick={useApproximateLocation}>Fill from location</button>
          <button type="submit">Save profile</button>
        </div>
        {profileMessage && <p className="empty-state">{profileMessage}</p>}
      </form>
      <div className="card">
        <div>
          <strong>{isInstalled ? "Installed" : "Install app"}</strong>
          <p>{isInstalled ? "Run Community Kenya is running as an app." : "Keep Run Community Kenya on your phone for quick session check-ins."}</p>
        </div>
        {canInstall && <button type="button" onClick={install}>Install</button>}
      </div>
      <p className="section-label">Recent activities</p>
      <div className="stack">
        {pending.length > 0 && (
          <div className="card warning-card">
            <div>
              <strong>{pending.length} pending sync</strong>
              <p>Saved locally from this device</p>
            </div>
            <button onClick={syncPending}>Sync</button>
          </div>
        )}
        {(stats?.recent?.length ? stats.recent : activities).map((activity) => (
          <div className="card" key={activity.id}>
            <div>
              <Link to={`/activities/${activity.id}`}><strong>{formatDistanceKm(activity.distance_meters)}</strong></Link>
              <p>{new Date(activity.started_at).toLocaleDateString()} - {activity.source}</p>
            </div>
            <div className="compact-actions">
              <span>{formatDuration(activity.duration_seconds)}</span>
              <button type="button" onClick={() => deleteActivity(activity.id)}>Delete</button>
            </div>
          </div>
        ))}
        {!activities.length && <div className="empty-state">No saved activities yet.</div>}
      </div>
      <button onClick={logout}>Log out</button>
    </section>
  );
}
