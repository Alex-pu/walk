export function formatDistanceKm(meters) {
  if (!meters) return "Distance open";
  return `${(meters / 1000).toFixed(1)} km`;
}

export function formatDuration(seconds) {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return [hrs, mins, secs].map((value) => String(value).padStart(2, "0")).join(":");
}

export function formatPace(seconds, meters) {
  if (!meters) return "-- /km";
  const secondsPerKm = seconds / (meters / 1000);
  const mins = Math.floor(secondsPerKm / 60);
  const secs = Math.round(secondsPerKm % 60);
  return `${mins}:${String(secs).padStart(2, "0")} /km`;
}

export function formatPaceFromSeconds(secondsPerKm) {
  if (!secondsPerKm) return "-- /km";
  const mins = Math.floor(secondsPerKm / 60);
  const secs = Math.round(secondsPerKm % 60);
  return `${mins}:${String(secs).padStart(2, "0")} /km`;
}

export function formatSessionTime(value) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}
