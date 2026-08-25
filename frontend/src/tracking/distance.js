const EARTH_RADIUS_M = 6371000;

function toRadians(value) {
  return (value * Math.PI) / 180;
}

export function distanceMeters(a, b) {
  const lat1 = toRadians(a.latitude);
  const lat2 = toRadians(b.latitude);
  const deltaLat = toRadians(b.latitude - a.latitude);
  const deltaLon = toRadians(b.longitude - a.longitude);
  const hav =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLon / 2) ** 2;
  return EARTH_RADIUS_M * 2 * Math.asin(Math.sqrt(hav));
}

export function isUsablePoint(previousPoint, nextPoint) {
  if (!nextPoint || nextPoint.accuracy > 50) return false;
  if (!previousPoint) return true;

  const segmentMeters = distanceMeters(previousPoint, nextPoint);
  const elapsedSeconds = Math.max((nextPoint.timestamp - previousPoint.timestamp) / 1000, 1);
  const metersPerSecond = segmentMeters / elapsedSeconds;

  if (segmentMeters < 3) return false;
  if (metersPerSecond > 8) return false;
  return true;
}

