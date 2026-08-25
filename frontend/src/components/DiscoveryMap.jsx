import L from "leaflet";
import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";

export default function DiscoveryMap({ crews, sessions }) {
  const elementRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!elementRef.current || mapRef.current) return;

    mapRef.current = L.map(elementRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView([-1.1452, 36.9561], 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(mapRef.current);
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    if (layerRef.current) {
      layerRef.current.remove();
    }

    const group = L.layerGroup();
    const points = [
      ...sessions.map((session) => ({
        lat: session.meeting_latitude,
        lng: session.meeting_longitude,
        label: session.title,
        type: session.activity_type,
      })),
      ...crews.map((crew) => ({
        lat: crew.meeting_latitude,
        lng: crew.meeting_longitude,
        label: crew.name,
        type: crew.activity_type,
      })),
    ].filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lng));

    points.forEach((point) => {
      L.circleMarker([point.lat, point.lng], {
        radius: 9,
        color: point.type === "run" ? "#b45309" : "#0f766e",
        fillColor: point.type === "run" ? "#f59e0b" : "#14b8a6",
        fillOpacity: 0.85,
        weight: 2,
      })
        .bindPopup(point.label)
        .addTo(group);
    });

    group.addTo(mapRef.current);
    layerRef.current = group;

    if (points.length) {
      const bounds = L.latLngBounds(points.map((point) => [point.lat, point.lng]));
      mapRef.current.fitBounds(bounds, { padding: [28, 28], maxZoom: 15 });
    }
  }, [crews, sessions]);

  return <div className="discovery-map" ref={elementRef} aria-label="Nearby crews and sessions map" />;
}
