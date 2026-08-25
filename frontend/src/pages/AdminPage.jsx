import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api/client.js";
import PageHero from "../components/PageHero.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function AdminPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [overview, setOverview] = useState({ users: [], crews: [], reports: [], crew_applications: [] });
  const [activeTab, setActiveTab] = useState("users");
  const [message, setMessage] = useState("");
  const [broadcastForm, setBroadcastForm] = useState({ subject: "", body: "" });

  function loadOverview() {
    api.adminOverview().then(setOverview).catch((error) => setMessage(error.message));
  }

  useEffect(() => {
    if (user.platform_role !== "admin") {
      return;
    }

    loadOverview();
  }, [user.platform_role]);

  function signOut() {
    logout();
    navigate("/login", { replace: true });
  }

  async function updateRole(targetUser, role) {
    setMessage("");
    try {
      await api.updatePlatformRole(targetUser.id, role);
      setMessage("User role updated.");
      loadOverview();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function reviewApplication(application, status) {
    setMessage("");
    try {
      await api.reviewCrewApplication(application.id, { status });
      setMessage(`Crew application ${status}.`);
      loadOverview();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function openSelfie(application) {
    setMessage("");
    try {
      const blob = await api.crewApplicationSelfie(application.id);
      window.open(URL.createObjectURL(blob), "_blank", "noopener,noreferrer");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function sendBroadcast(event) {
    event.preventDefault();
    setMessage("");
    try {
      const response = await api.sendBroadcast(broadcastForm);
      setMessage(`Broadcast processed: ${response.sent} sent, ${response.failed} failed.`);
      setBroadcastForm({ subject: "", body: "" });
    } catch (error) {
      setMessage(error.message);
    }
  }

  if (user.platform_role !== "admin") {
    return (
      <section className="page">
        <div className="empty-state">
          <strong>Platform admin access required.</strong>
          <span>
            Signed in as {user.email || "unknown account"} with role {user.platform_role || "unknown"}.
          </span>
          <button type="button" onClick={signOut}>Sign out</button>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <PageHero eyebrow="Admin" title="Platform overview">
        <p>Manage platform roles, inspect crews, and review safety reports.</p>
      </PageHero>
      {message && <p className="empty-state">{message}</p>}
      <div className="metric-grid">
        <div><strong>{overview.users.length}</strong><span>Users</span></div>
        <div><strong>{overview.crews.length}</strong><span>Crews</span></div>
        <div><strong>{overview.crew_applications.filter((application) => application.status === "pending").length}</strong><span>Pending applications</span></div>
      </div>

      <div className="segmented-control">
        <button className={activeTab === "users" ? "active-filter" : ""} onClick={() => setActiveTab("users")}>Users</button>
        <button className={activeTab === "crews" ? "active-filter" : ""} onClick={() => setActiveTab("crews")}>Crews</button>
        <button className={activeTab === "applications" ? "active-filter" : ""} onClick={() => setActiveTab("applications")}>Applications</button>
        <button className={activeTab === "broadcast" ? "active-filter" : ""} onClick={() => setActiveTab("broadcast")}>Broadcast</button>
        <button className={activeTab === "reports" ? "active-filter" : ""} onClick={() => setActiveTab("reports")}>Reports</button>
      </div>

      {activeTab === "users" && (
        <>
          <p className="section-label">Users</p>
          <div className="stack">
            {overview.users.map((targetUser) => (
              <div className="admin-row" key={targetUser.id}>
                <div>
                  <strong>{targetUser.name}</strong>
                  <p>{targetUser.email}</p>
                  <p>{targetUser.neighborhood}</p>
                </div>
                <span className={`status-pill ${targetUser.platform_role === "admin" ? "status-active" : ""}`}>
                  {targetUser.platform_role}
                </span>
                {targetUser.id !== user.id ? (
                  <div className="compact-actions">
                    {targetUser.platform_role !== "admin" && (
                      <button type="button" onClick={() => updateRole(targetUser, "admin")}>Make admin</button>
                    )}
                    {targetUser.platform_role === "admin" && (
                      <button type="button" onClick={() => updateRole(targetUser, "member")}>Make member</button>
                    )}
                  </div>
                ) : (
                  <span className="status-pill">You</span>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === "crews" && (
        <>
          <p className="section-label">Crews</p>
          <div className="stack">
            {overview.crews.map((crew) => (
              <Link className="admin-row" to={`/crews/${crew.id}`} key={crew.id}>
                <div>
                  <strong>{crew.name}</strong>
                  <p>{crew.meeting_point_name}</p>
                  <p>{crew.activity_type} - {crew.visibility}</p>
                </div>
                <div className="card-meta">
                  <span>{crew.member_count} members</span>
                  <span>Open</span>
                </div>
              </Link>
            ))}
            {!overview.crews.length && <div className="empty-state">No crews yet.</div>}
          </div>
        </>
      )}

      {activeTab === "applications" && (
        <>
          <p className="section-label">Crew applications</p>
          <div className="stack">
            {overview.crew_applications.map((application) => (
              <div className="admin-row" key={application.id}>
                <div>
                  <strong>{application.proposed_name}</strong>
                  <p>{application.applicant_name} - {application.applicant_email}</p>
                  <p>{application.locality} - {application.meeting_point_name}</p>
                  <p>{application.activity_type} - {application.visibility} - ID: {application.id_number}</p>
                  {application.description && <p>{application.description}</p>}
                  {application.admin_note && <p>{application.admin_note}</p>}
                </div>
                <span className={`status-pill status-${application.status}`}>{application.status}</span>
                <div className="compact-actions">
                  {application.has_selfie && (
                    <button type="button" onClick={() => openSelfie(application)}>View selfie</button>
                  )}
                  {application.status === "pending" && (
                    <>
                      <button type="button" onClick={() => reviewApplication(application, "approved")}>Approve</button>
                      <button type="button" onClick={() => reviewApplication(application, "denied")}>Deny</button>
                    </>
                  )}
                  {application.crew_id && <Link className="button-link" to={`/crews/${application.crew_id}`}>Open crew</Link>}
                </div>
              </div>
            ))}
            {!overview.crew_applications.length && <div className="empty-state">No crew applications yet.</div>}
          </div>
        </>
      )}

      {activeTab === "broadcast" && (
        <>
          <p className="section-label">Email broadcast</p>
          <form className="compact-form" onSubmit={sendBroadcast}>
            <input
              placeholder="Subject"
              value={broadcastForm.subject}
              onChange={(event) => setBroadcastForm({ ...broadcastForm, subject: event.target.value })}
            />
            <textarea
              placeholder="Message"
              value={broadcastForm.body}
              onChange={(event) => setBroadcastForm({ ...broadcastForm, body: event.target.value })}
            />
            <button type="submit">Send to all users</button>
          </form>
        </>
      )}

      {activeTab === "reports" && (
        <>
          <p className="section-label">Reports</p>
          <div className="stack">
            {overview.reports.map((report) => (
              <div className="admin-row warning-card" key={report.id}>
                <div>
                  <strong>{report.reason}</strong>
                  <p>{report.reporter_name} reported {report.reported_name}</p>
                  <p>{report.crew_name || "No crew"} - {report.status}</p>
                  {report.details && <p>{report.details}</p>}
                </div>
                {report.crew_id && <Link className="button-link" to={`/crews/${report.crew_id}`}>Open crew</Link>}
              </div>
            ))}
            {!overview.reports.length && <div className="empty-state">No reports yet.</div>}
          </div>
        </>
      )}
    </section>
  );
}
