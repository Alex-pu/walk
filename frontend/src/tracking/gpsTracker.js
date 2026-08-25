import { clearActiveActivity, loadActiveActivity, saveActiveActivity } from "./activityStorage.js";
import { distanceMeters, isUsablePoint } from "./distance.js";

export function createGpsTracker({ onUpdate, getTimerSnapshot } = {}) {
  let watchId = null;
  let status = "idle";
  let route = [];
  let totalMeters = 0;
  let startedAt = null;

  function persist() {
    const snapshot = {
      status,
      route,
      totalMeters,
      startedAt,
      timer: getTimerSnapshot?.() || null,
      updatedAt: Date.now(),
    };
    saveActiveActivity(snapshot).catch(() => {});
    onUpdate?.(snapshot);
  }

  function handlePosition(position) {
    if (status !== "active") return;
    const nextPoint = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      timestamp: position.timestamp,
      accuracy: position.coords.accuracy,
    };
    const previousPoint = route[route.length - 1];
    if (!isUsablePoint(previousPoint, nextPoint)) return;
    if (previousPoint) totalMeters += distanceMeters(previousPoint, nextPoint);
    route = [...route, nextPoint];
    persist();
  }

  function startWatching() {
    if (!navigator.geolocation || watchId !== null) return;
    watchId = navigator.geolocation.watchPosition(handlePosition, () => {
      status = "error";
      persist();
    }, { enableHighAccuracy: true, maximumAge: 0, timeout: 15000 });
  }

  return {
    async restore() {
      const saved = await loadActiveActivity();
      if (!saved) return null;
      status = saved.status || "idle";
      route = saved.route || [];
      totalMeters = saved.totalMeters || 0;
      startedAt = saved.startedAt || null;
      onUpdate?.({ status, route, totalMeters, startedAt, updatedAt: saved.updatedAt });
      return saved;
    },
    start() {
      if (!navigator.geolocation) {
        status = "unsupported";
        persist();
        return;
      }
      startedAt = Date.now();
      status = "active";
      route = [];
      totalMeters = 0;
      startWatching();
      persist();
    },
    pause() {
      status = "paused";
      persist();
    },
    resume() {
      status = "active";
      startWatching();
      persist();
    },
    finish() {
      if (watchId !== null) navigator.geolocation.clearWatch(watchId);
      status = "finished";
      clearActiveActivity().catch(() => {});
      return { route, distance_meters: totalMeters, started_at: startedAt };
    },
    getDistance() {
      return totalMeters;
    },
    getRoute() {
      return route;
    },
    getStatus() {
      return status;
    },
  };
}
