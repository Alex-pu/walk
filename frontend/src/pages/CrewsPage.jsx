import { useEffect, useState } from "react";

import { api } from "../api/client.js";
import CrewCard from "../components/CrewCard.jsx";
import PageHero from "../components/PageHero.jsx";
import PlacePicker from "../components/PlacePicker.jsx";

const initialForm = {
  proposed_name: "",
  description: "",
  activity_type: "walk",
  visibility: "public",
  meeting_point_name: "",
  meeting_latitude: "",
  meeting_longitude: "",
  locality: "",
  id_number: "",
  selfie: null,
};

export default function CrewsPage() {
  const [crews, setCrews] = useState([]);
  const [applications, setApplications] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  function loadCrews() {
    api.crews().then((data) => setCrews(data.crews)).catch(() => setCrews([]));
  }

  function loadApplications() {
    api.myCrewApplications().then((data) => setApplications(data.applications)).catch(() => setApplications([]));
  }

  useEffect(() => {
    loadCrews();
    loadApplications();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!form.meeting_latitude || !form.meeting_longitude) {
      setError("Search and choose the crew meeting place before submitting.");
      return;
    }
    try {
      const payload = new FormData();
      Object.entries(form).forEach(([key, value]) => {
        if (value !== null && value !== "") {
          payload.append(key, value);
        }
      });
      await api.submitCrewApplication(payload);
      setForm(initialForm);
      event.target.reset();
      setMessage("Application submitted. An admin will review it before the crew goes live.");
      loadApplications();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="page">
      <PageHero eyebrow="Crews" title="Your neighborhood groups" />
      <form className="compact-form" onSubmit={handleSubmit}>
        <input placeholder="Crew name" value={form.proposed_name} onChange={(event) => setForm({ ...form, proposed_name: event.target.value })} />
        <select value={form.activity_type} onChange={(event) => setForm({ ...form, activity_type: event.target.value })}>
          <option value="walk">Walk</option>
          <option value="run">Run</option>
          <option value="mixed">Mixed</option>
        </select>
        <select value={form.visibility} onChange={(event) => setForm({ ...form, visibility: event.target.value })}>
          <option value="public">Public</option>
          <option value="private">Private</option>
        </select>
        <input placeholder="Locality / neighborhood" value={form.locality} onChange={(event) => setForm({ ...form, locality: event.target.value })} />
        <PlacePicker
          label="Meeting point"
          value={form.meeting_point_name}
          onChange={(place) =>
            setForm({
              ...form,
              meeting_point_name: place.name,
              meeting_latitude: place.latitude ?? form.meeting_latitude,
              meeting_longitude: place.longitude ?? form.meeting_longitude,
            })
          }
        />
        {form.meeting_latitude && form.meeting_longitude && (
          <p className="field-hint">Selected location saved for map discovery.</p>
        )}
        <textarea placeholder="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        <input placeholder="National ID number" value={form.id_number} onChange={(event) => setForm({ ...form, id_number: event.target.value })} />
        <label>
          Selfie photo
          <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setForm({ ...form, selfie: event.target.files[0] || null })} />
        </label>
        {error && <p className="error">{error}</p>}
        {message && <p className="empty-state">{message}</p>}
        <button type="submit">Apply to create crew</button>
      </form>
      {!!applications.length && (
        <>
          <p className="section-label">Your applications</p>
          <div className="stack">
            {applications.map((application) => (
              <div className="admin-row" key={application.id}>
                <div>
                  <strong>{application.proposed_name}</strong>
                  <p>{application.locality} - {application.meeting_point_name}</p>
                  {application.admin_note && <p>{application.admin_note}</p>}
                </div>
                <span className={`status-pill status-${application.status}`}>{application.status}</span>
              </div>
            ))}
          </div>
        </>
      )}
      <div className="stack">
        {crews.map((crew) => (
          <CrewCard key={crew.id} crew={crew} />
        ))}
      </div>
    </section>
  );
}
