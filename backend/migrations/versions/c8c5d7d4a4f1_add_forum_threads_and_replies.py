"""add forum threads and replies

Revision ID: c8c5d7d4a4f1
Revises: bbf9c32d8218
Create Date: 2026-08-24 16:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c8c5d7d4a4f1"
down_revision = "bbf9c32d8218"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "forum_threads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("crew_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["crew_id"], ["crews.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forum_threads_scope", "forum_threads", ["scope_type", "crew_id"])
    op.create_index("ix_forum_threads_status", "forum_threads", ["status"])

    op.create_table(
        "forum_replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("parent_reply_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["parent_reply_id"], ["forum_replies.id"]),
        sa.ForeignKeyConstraint(["thread_id"], ["forum_threads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forum_replies_thread", "forum_replies", ["thread_id"])
    op.create_index("ix_forum_replies_parent", "forum_replies", ["parent_reply_id"])


def downgrade():
    op.drop_index("ix_forum_replies_parent", table_name="forum_replies")
    op.drop_index("ix_forum_replies_thread", table_name="forum_replies")
    op.drop_table("forum_replies")
    op.drop_index("ix_forum_threads_status", table_name="forum_threads")
    op.drop_index("ix_forum_threads_scope", table_name="forum_threads")
    op.drop_table("forum_threads")
