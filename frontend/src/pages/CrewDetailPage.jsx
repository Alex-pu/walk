import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Clock, MapPinned, Share2, Trophy, Users, Zap } from "lucide-react";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import PlacePicker from "../components/PlacePicker.jsx";
import SessionCard from "../components/SessionCard.jsx";
import StatTile from "../components/StatTile.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDistanceKm, formatDuration } from "../utils/format.js";

export default function CrewDetailPage() {
  const { user } = useAuth();
  const { crewId } = useParams();
  const [crew, setCrew] = useState(null);
  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [sessionForm, setSessionForm] = useState({
    title: "",
    activity_type: "walk",
    scheduled_start: "",
    expected_distance_km: "",
    difficulty: "easy",
    meeting_point_name: "",
    meeting_latitude: "",
    meeting_longitude: "",
  });
  const [formMessage, setFormMessage] = useState("");

  function loadCrew() {
    api.crew(crewId).then((data) => setCrew(data.crew));
    api.crewStats(crewId).then((data) => setStats(data.month)).catch(() => setStats(null));
    api.crewReports(crewId).then((data) => setReports(data.reports)).catch(() => setReports([]));
  }

  useEffect(() => {
    loadCrew();
  }, [crewId]);

  useEffect(() => {
    if (!crew) return;
    setSessionForm((current) => ({
      ...current,
      activity_type: crew.activity_type === "mixed" ? "walk" : crew.activity_type,
      meeting_point_name: current.meeting_point_name || crew.meeting_point_name,
      meeting_latitude: current.meeting_latitude || String(crew.meeting_latitude),
      meeting_longitude: current.meeting_longitude || String(crew.meeting_longitude),
    }));
  }, [crew]);

  async function createSession(event) {
    event.preventDefault();
    setFormMessage("");
    if (!sessionForm.meeting_latitude || !sessionForm.meeting_longitude) {
      setFormMessage("Search and choose the session meeting point before creating it.");
      return;
    }
    try {
      await api.createSession(crewId, {
        title: sessionForm.title,
        activity_type: sessionForm.activity_type,
        scheduled_start: new Date(sessionForm.scheduled_start).toISOString(),
        expected_distance_m: sessionForm.expected_distance_km
          ? Math.round(Number(sessionForm.expected_distance_km) * 1000)
          : null,
        difficulty: sessionForm.difficulty,
        meeting_point_name: sessionForm.meeting_point_name,
        meeting_latitude: sessionForm.meeting_latitude,
        meeting_longitude: sessionForm.meeting_longitude,
      });
      setSessionForm((current) => ({ ...current, title: "", scheduled_start: "", expected_distance_km: "" }));
      setFormMessage("Session created.");
      loadCrew();
    } catch (error) {
      setFormMessage(error.message);
    }
  }

  function updateSessionForm(field, value) {
    setSessionForm((current) => ({ ...current, [field]: value }));
  }

  async function reportMember(member) {
    setFormMessage("");
    try {
      await api.reportUser({
        reported_user_id: member.user_id,
        crew_id: Number(crewId),
        reason: "unsafe_behavior",
        details: `Report from ${crew.name}`,
      });
      setFormMessage("Report submitted.");
    } catch (error) {
      setFormMessage(error.message);
    }
  }

  async function blockMember(member) {
    setFormMessage("");
    try {
      await api.blockUser({ blocked_user_id: member.user_id });
      setFormMessage("Member blocked.");
    } catch (error) {
      setFormMessage(error.message);
    }
  }

  async function updateMemberRole(member, role) {
    setFormMessage("");
    try {
      await api.updateCrewMemberRole(crewId, member.user_id, role);
      setFormMessage("Crew role updated.");
      loadCrew();
    } catch (error) {
      setFormMessage(error.message);
    }
  }

  async function shareCrewInvite() {
    const inviteUrl = `${window.location.origin}/join/crew/${crewId}`;
    setFormMessage("");
    try {
      if (navigator.share) {
        await navigator.share({
          title: `Join ${crew.name} on Run Community Kenya`,
          text: `Join my Run Community Kenya crew: ${crew.name}`,
          url: inviteUrl,
        });
        return;
      }
      await navigator.clipboard.writeText(inviteUrl);
      setFormMessage("Crew invite link copied.");
    } catch (error) {
      setFormMessage("Could not share the invite link.");
    }
  }

  if (!crew) return <section className="page">Loading...</section>;

  return (
    <section className="page">
      <PageHero eyebrow={crew.activity_type} title={crew.name}>
        <p>{crew.description}</p>
      </PageHero>
      <div className="action-row">
        <button onClick={() => api.joinCrew(crewId).then(loadCrew)}>Join crew</button>
        <button type="button" onClick={shareCrewInvite}>
          <Share2 size={18} aria-hidden="true" />
          Share invite
        </button>
        {(crew.current_user_role || user.platform_role === "admin") && (
          <Link className="button-link" to={`/crews/${crewId}/forum`}>Crew forum</Link>
        )}
      </div>
      <div className="metric-grid">
        <StatTile icon={MapPinned} value={formatDistanceKm(stats?.distance_meters || 0)} label="Month km" tone="accent" />
        <StatTile icon={Clock} value={formatDuration(stats?.duration_seconds || 0)} label="Active time" />
        <StatTile icon={Trophy} value={stats?.completed_sessions || 0} label="Completed" />
      </div>
      <div className="metric-grid">
        <StatTile icon={Zap} value={stats?.activity_count || 0} label="Activities" />
        <StatTile icon={Users} value={stats?.active_members || 0} label="Active members" />
        <StatTile icon={Users} value={crew.member_count} label="Total members" />
      </div>
      <p className="section-label">Upcoming sessions</p>
      <div className="stack">
        {crew.sessions?.map((session) => (
          <SessionCard key={session.id} session={session} />
        ))}
        {!crew.sessions?.length && <div className="empty-state">No upcoming sessions yet.</div>}
      </div>
      <p className="section-label">Members</p>
      <div className="stack">
        {crew.members.map((member) => (
          <div className="card" key={member.id}>
            <div>
              <strong>{member.name}</strong>
              <p>{member.role} - {member.status}</p>
            </div>
            {member.user_id !== user.id ? (
              <div className="compact-actions">
                <button type="button" onClick={() => reportMember(member)}>Report</button>
                <button type="button" onClick={() => blockMember(member)}>Block</button>
                {crew.can_manage_members && member.role !== "organizer" && (
                  <button type="button" onClick={() => updateMemberRole(member, "organizer")}>Promote</button>
                )}
                {crew.can_manage_members && member.role === "organizer" && (
                  <button type="button" onClick={() => updateMemberRole(member, "member")}>Demote</button>
                )}
              </div>
            ) : (
              <span className="status-pill">You</span>
            )}
          </div>
        ))}
      </div>
      {(crew.can_create_sessions || user.platform_role === "admin") && (
        <>
          <p className="section-label">Crew reports</p>
          <div className="stack">
            {reports.map((report) => (
              <div className="card" key={report.id}>
                <div>
                  <strong>{report.reason}</strong>
                  <p>{report.reporter_name} reported {report.reported_name}</p>
                  <p>{report.details || "No details"} - {report.status}</p>
                </div>
              </div>
            ))}
            {!reports.length && <div className="empty-state">No reports for this crew.</div>}
          </div>
        </>
      )}
      <p className="section-label">Create a session</p>
      {crew.can_create_sessions ? (
        <form className="compact-form" onSubmit={createSession}>
          <input
            placeholder="Session title"
            value={sessionForm.title}
            onChange={(event) => updateSessionForm("title", event.target.value)}
            required
          />
          <div className="form-grid">
            <select value={sessionForm.activity_type} onChange={(event) => updateSessionForm("activity_type", event.target.value)}>
              <option value="walk">Walk</option>
              <option value="run">Run</option>
              <option value="mixed">Mixed</option>
            </select>
            <select value={sessionForm.difficulty} onChange={(event) => updateSessionForm("difficulty", event.target.value)}>
              <option value="easy">Easy</option>
              <option value="moderate">Moderate</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div className="form-grid">
            <input
              type="datetime-local"
              value={sessionForm.scheduled_start}
              onChange={(event) => updateSessionForm("scheduled_start", event.target.value)}
              required
            />
            <input
              type="number"
              min="0"
              step="0.1"
              placeholder="Distance km"
              value={sessionForm.expected_distance_km}
              onChange={(event) => updateSessionForm("expected_distance_km", event.target.value)}
            />
          </div>
          <PlacePicker
            label="Meeting point"
            value={sessionForm.meeting_point_name}
            onChange={(place) =>
              setSessionForm((current) => ({
                ...current,
                meeting_point_name: place.name,
                meeting_latitude: place.latitude ?? current.meeting_latitude,
                meeting_longitude: place.longitude ?? current.meeting_longitude,
              }))
            }
          />
          {sessionForm.meeting_latitude && sessionForm.meeting_longitude && (
            <p className="field-hint">Selected location saved for this session.</p>
          )}
          {formMessage && <p className="empty-state">{formMessage}</p>}
          <button type="submit">Create session</button>
        </form>
      ) : (
        <div className="empty-state">Only crew organizers can create sessions.</div>
      )}
      {!crew.can_create_sessions && formMessage && <p className="empty-state">{formMessage}</p>}
    </section>
  );
}
