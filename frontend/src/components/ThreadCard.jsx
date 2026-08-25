import { Link } from "react-router-dom";
import { MessageCircle, Pin } from "lucide-react";

export default function ThreadCard({ thread }) {
  return (
    <Link className="thread-card" to={`/forum/${thread.id}`}>
      <div className="thread-icon">
        {thread.pinned ? <Pin size={22} aria-hidden="true" /> : <MessageCircle size={22} aria-hidden="true" />}
      </div>
      <div className="thread-card-main">
        <div className="mini-meta-row">
          <span>{thread.category}</span>
          <span>{thread.status}</span>
          {thread.crew_name && <span>{thread.crew_name}</span>}
        </div>
        <h3>{thread.title}</h3>
        <p>{thread.author_name || "Community member"}</p>
      </div>
      <strong className="thread-count">{thread.reply_count}</strong>
    </Link>
  );
}
