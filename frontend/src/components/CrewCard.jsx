import { Link } from "react-router-dom";

export default function CrewCard({ crew }) {
  return (
    <Link className="card crew-card" to={`/crews/${crew.id}`}>
      <div>
        <p className="eyebrow">{crew.activity_type}</p>
        <h3>{crew.name}</h3>
        <p>{crew.meeting_point_name}</p>
      </div>
      <strong>{crew.member_count} members</strong>
    </Link>
  );
}

