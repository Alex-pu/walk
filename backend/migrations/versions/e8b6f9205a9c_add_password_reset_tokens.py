"""add password reset tokens

Revision ID: e8b6f9205a9c
Revises: d1a7c54f0b32
Create Date: 2026-08-25 14:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e8b6f9205a9c"
down_revision = "d1a7c54f0b32"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=160), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_reset_tokens_token", "password_reset_tokens", ["token"], unique=True)


def downgrade():
    op.drop_index("ix_password_reset_tokens_token", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
