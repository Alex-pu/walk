import { useEffect, useState } from "react";

import { api } from "../api/client.js";
import CrewCard from "../components/CrewCard.jsx";
import DiscoveryMap from "../components/DiscoveryMap.jsx";
import PageHero from "../components/PageHero.jsx";
import SessionCard from "../components/SessionCard.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function DiscoverPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [crews, setCrews] = useState([]);
  const [filters, setFilters] = useState({ day: "all", activity: "all", difficulty: "all", radius_km: 10 });
  const [view, setView] = useState("list");
  const [coords, setCoords] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const discoveryCoords = coords || (
      user?.latitude && user?.longitude ? { latitude: user.latitude, longitude: user.longitude } : null
    );
    const params = discoveryCoords
      ? { latitude: discoveryCoords.latitude, longitude: discoveryCoords.longitude, radius_km: filters.radius_km }
      : {};
    Promise.all([api.nearbySessions(params), api.nearbyCrews(params)])
      .then(([sessionData, crewData]) => {
        setSessions(sessionData.sessions);
        setCrews(crewData.crews);
      })
      .catch(() => {
        setSessions([]);
        setCrews([]);
      });
  }, [coords, user?.latitude, user?.longitude, filters.radius_km]);

  function useLocation() {
    setMessage("");
    if (!navigator.geolocation) {
      setMessage("Location is not available in this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      () => setMessage("Location permission was not granted."),
      { enableHighAccuracy: true, timeout: 12000 }
    );
  }

  function isSameDay(value, offsetDays) {
    const date = new Date(value);
    const target = new Date();
    target.setDate(target.getDate() + offsetDays);
    return date.toDateString() === target.toDateString();
  }

  const filteredSessions = sessions.filter((session) => {
    if (filters.activity !== "all" && session.activity_type !== filters.activity) return false;
    if (filters.difficulty !== "all" && session.difficulty !== filters.difficulty) return false;
    if (filters.day === "today" && !isSameDay(session.scheduled_start, 0)) return false;
    if (filters.day === "tomorrow" && !isSameDay(session.scheduled_start, 1)) return false;
    return true;
  });

  const filteredCrews = crews.filter((crew) => {
    if (filters.activity !== "all" && crew.activity_type !== filters.activity && crew.activity_type !== "mixed") return false;
    return true;
  });

  function toggleFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: current[key] === value ? "all" : value }));
  }

  return (
    <section className="page">
      <PageHero eyebrow="Discover" title="Find a walk or run" />
      <div className="filter-row">
        <button className={filters.day === "today" ? "active-filter" : ""} onClick={() => toggleFilter("day", "today")}>Today</button>
        <button className={filters.day === "tomorrow" ? "active-filter" : ""} onClick={() => toggleFilter("day", "tomorrow")}>Tomorrow</button>
        <button className={filters.activity === "walk" ? "active-filter" : ""} onClick={() => toggleFilter("activity", "walk")}>Walk</button>
        <button className={filters.activity === "run" ? "active-filter" : ""} onClick={() => toggleFilter("activity", "run")}>Run</button>
        <button className={filters.difficulty === "easy" ? "active-filter" : ""} onClick={() => toggleFilter("difficulty", "easy")}>Beginner</button>
      </div>
      <div className="toolbar-row">
        <select value={filters.radius_km} onChange={(event) => setFilters({ ...filters, radius_km: Number(event.target.value) })}>
          <option value={3}>3 km radius</option>
          <option value={5}>5 km radius</option>
          <option value={10}>10 km radius</option>
          <option value={20}>20 km radius</option>
        </select>
        <button onClick={useLocation}>{coords ? "Live location set" : user?.latitude ? "Use live location" : "Use location"}</button>
      </div>
      {!coords && user?.latitude && <p className="gps-status">Using your saved approximate location.</p>}
      <div className="segmented-control">
        <button className={view === "list" ? "active-filter" : ""} onClick={() => setView("list")}>List</button>
        <button className={view === "map" ? "active-filter" : ""} onClick={() => setView("map")}>Map</button>
      </div>
      {message && <p className="empty-state">{message}</p>}

      {view === "map" ? (
        <DiscoveryMap crews={filteredCrews} sessions={filteredSessions} />
      ) : (
        <>
          <p className="section-label">Upcoming sessions</p>
          <div className="stack">
            {filteredSessions.map((session) => (
              <SessionCard key={session.id} session={session} />
            ))}
            {!filteredSessions.length && <div className="empty-state">No sessions match these filters.</div>}
          </div>
          <p className="section-label">Crews</p>
          <div className="stack">
            {filteredCrews.map((crew) => (
              <CrewCard key={crew.id} crew={crew} />
            ))}
            {!filteredCrews.length && <div className="empty-state">No crews match these filters.</div>}
          </div>
        </>
      )}
    </section>
  );
}
