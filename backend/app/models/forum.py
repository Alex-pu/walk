from datetime import datetime, timezone

from app.extensions import db


class ForumThread(db.Model):
    __tablename__ = "forum_threads"

    id = db.Column(db.Integer, primary_key=True)
    scope_type = db.Column(db.String(20), nullable=False, default="platform")
    crew_id = db.Column(db.Integer, db.ForeignKey("crews.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), nullable=False, default="general")
    status = db.Column(db.String(20), nullable=False, default="open")
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    author = db.relationship("User")
    crew = db.relationship("Crew")
    replies = db.relationship("ForumReply", back_populates="thread", cascade="all, delete-orphan")

    def to_dict(self, include_body=True, include_replies=False):
        data = {
            "id": self.id,
            "scope_type": self.scope_type,
            "crew_id": self.crew_id,
            "crew_name": self.crew.name if self.crew else None,
            "author_id": self.author_id,
            "author_name": self.author.name if self.author else None,
            "title": self.title,
            "category": self.category,
            "status": self.status,
            "pinned": self.pinned,
            "reply_count": len(self.replies),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_body:
            data["body"] = self.body
        if include_replies:
            data["replies"] = [reply.to_dict() for reply in self.replies]
        return data


class ForumReply(db.Model):
    __tablename__ = "forum_replies"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("forum_threads.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    parent_reply_id = db.Column(db.Integer, db.ForeignKey("forum_replies.id"))
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    thread = db.relationship("ForumThread", back_populates="replies")
    author = db.relationship("User")
    parent = db.relationship(
        "ForumReply",
        remote_side=[id],
        backref="children",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "author_id": self.author_id,
            "author_name": self.author.name if self.author else None,
            "parent_reply_id": self.parent_reply_id,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
