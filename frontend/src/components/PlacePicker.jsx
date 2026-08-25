import { useState } from "react";

const NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";

function resultLabel(result) {
  return result.display_name || result.name || "Unnamed place";
}

export default function PlacePicker({ label = "Place", placeholder = "Search for a place in Kenya", value, onChange }) {
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  async function searchPlaces() {
    const query = value?.trim();
    if (!query) {
      setStatus("Enter a place name first.");
      setResults([]);
      return;
    }

    setIsSearching(true);
    setStatus("");
    setResults([]);

    try {
      const params = new URLSearchParams({
        q: query,
        format: "jsonv2",
        addressdetails: "1",
        countrycodes: "ke",
        limit: "6",
      });
      const response = await fetch(`${NOMINATIM_URL}?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Place search is unavailable right now.");
      }
      const data = await response.json();
      setResults(data);
      setStatus(data.length ? "Choose the correct result." : "No matching places found.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsSearching(false);
    }
  }

  function choosePlace(result) {
    const labelText = resultLabel(result);
    onChange({
      name: labelText,
      address: labelText,
      latitude: Number(Number(result.lat).toFixed(6)),
      longitude: Number(Number(result.lon).toFixed(6)),
    });
    setResults([]);
    setStatus("Place selected.");
  }

  return (
    <div className="place-picker">
      <label>
        {label}
        <span className="place-search-row">
          <input
            placeholder={placeholder}
            value={value}
            onChange={(event) => {
              onChange({ name: event.target.value, latitude: "", longitude: "" });
              setResults([]);
              setStatus("");
            }}
          />
          <button type="button" onClick={searchPlaces} disabled={isSearching}>
            {isSearching ? "Searching" : "Search"}
          </button>
        </span>
      </label>
      {status && <span className="field-hint">{status}</span>}
      {!!results.length && (
        <div className="place-results">
          {results.map((result) => (
            <button type="button" key={result.place_id} onClick={() => choosePlace(result)}>
              {resultLabel(result)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
