import L from "leaflet";
import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";

export default function RouteMap({ points }) {
  const elementRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!elementRef.current || mapRef.current) return;

    mapRef.current = L.map(elementRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView([-1.1452, 36.9561], 14);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(mapRef.current);
    window.setTimeout(() => mapRef.current?.invalidateSize(), 0);
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    if (layerRef.current) {
      layerRef.current.remove();
      layerRef.current = null;
    }

    if (!points.length) {
      mapRef.current.setView([-1.1452, 36.9561], 14);
      return;
    }

    const latLngs = points.map((point) => [point.latitude, point.longitude]);
    layerRef.current = L.layerGroup().addTo(mapRef.current);
    if (latLngs.length === 1) {
      L.circleMarker(latLngs[0], {
        radius: 9,
        color: "#0f766e",
        fillColor: "#14b8a6",
        fillOpacity: 0.85,
        weight: 2,
      }).addTo(layerRef.current);
      mapRef.current.setView(latLngs[0], 16);
      return;
    }

    const route = L.polyline(latLngs, { color: "#0f766e", weight: 5 }).addTo(layerRef.current);
    mapRef.current.fitBounds(route.getBounds(), { padding: [24, 24], maxZoom: 17 });
  }, [points]);

  return <div className="route-map" ref={elementRef} aria-label="Activity route map" />;
}
