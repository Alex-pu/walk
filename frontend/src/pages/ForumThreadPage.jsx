import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client.js";
import FormattedText from "../components/FormattedText.jsx";
import PageHero from "../components/PageHero.jsx";

function ReplyItem({ reply, onReply }) {
  return (
    <div className="reply-item">
      <div>
        <strong>{reply.author_name || "Community member"}</strong>
        <FormattedText text={reply.body} />
      </div>
      <button type="button" onClick={() => onReply(reply)}>Reply</button>
      {!!reply.children?.length && (
        <div className="reply-children">
          {reply.children.map((child) => (
            <ReplyItem key={child.id} reply={child} onReply={onReply} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ForumThreadPage() {
  const { threadId } = useParams();
  const [thread, setThread] = useState(null);
  const [replyBody, setReplyBody] = useState("");
  const [replyTarget, setReplyTarget] = useState(null);
  const [message, setMessage] = useState("");

  function loadThread() {
    api.forumThread(threadId).then((data) => setThread(data.thread)).catch((error) => setMessage(error.message));
  }

  useEffect(() => {
    loadThread();
  }, [threadId]);

  async function createReply(event) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createForumReply(threadId, {
        body: replyBody,
        parent_reply_id: replyTarget?.id || null,
      });
      setReplyBody("");
      setReplyTarget(null);
      loadThread();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function updateThread(payload) {
    setMessage("");
    try {
      const data = await api.updateForumThread(threadId, payload);
      setThread((current) => ({ ...current, ...data.thread }));
    } catch (error) {
      setMessage(error.message);
    }
  }

  if (!thread) return <section className="page">{message || "Loading..."}</section>;

  return (
    <section className="page">
      <PageHero eyebrow={thread.scope_type === "crew" ? thread.crew_name : "Community forum"} title={thread.title}>
        <p>{thread.author_name || "Community member"}</p>
        {thread.scope_type === "crew" && <Link className="subtle-link" to={`/crews/${thread.crew_id}/forum`}>Back to crew forum</Link>}
        {thread.scope_type === "platform" && <Link className="subtle-link" to="/forum">Back to forum</Link>}
      </PageHero>

      <div className="thread-body">
        <div className="mini-meta-row">
          {thread.pinned && <span>Pinned</span>}
          <span>{thread.category}</span>
          <span>{thread.status}</span>
        </div>
        <FormattedText text={thread.body} />

        {thread.can_moderate && (
          <div className="compact-actions">
            <button type="button" onClick={() => updateThread({ pinned: !thread.pinned })}>
              {thread.pinned ? "Unpin" : "Pin"}
            </button>
            <button type="button" onClick={() => updateThread({ status: "open" })}>Open</button>
            <button type="button" onClick={() => updateThread({ status: "resolved" })}>Resolve</button>
            <button type="button" onClick={() => updateThread({ status: "closed" })}>Close</button>
          </div>
        )}

        <form className="inline-reply-form" onSubmit={createReply}>
          {replyTarget && (
            <div className="reply-target">
              <span>Replying to {replyTarget.author_name || "community member"}</span>
              <button type="button" onClick={() => setReplyTarget(null)}>Cancel</button>
            </div>
          )}
          <textarea
            placeholder={thread.status === "closed" ? "This thread is closed" : "Write a reply"}
            value={replyBody}
            onChange={(event) => setReplyBody(event.target.value)}
            disabled={thread.status === "closed"}
            required
          />
          {message && <p className="empty-state">{message}</p>}
          <button type="submit" disabled={thread.status === "closed"}>Post reply</button>
        </form>
      </div>

      <p className="section-label">Replies</p>
      <div className="reply-list">
        {thread.replies.map((reply) => (
          <ReplyItem key={reply.id} reply={reply} onReply={setReplyTarget} />
        ))}
        {!thread.replies.length && <div className="empty-state">No replies yet.</div>}
      </div>
    </section>
  );
}
