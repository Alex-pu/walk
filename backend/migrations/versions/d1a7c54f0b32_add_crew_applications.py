"""add crew applications

Revision ID: d1a7c54f0b32
Revises: c8c5d7d4a4f1
Create Date: 2026-08-25 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d1a7c54f0b32"
down_revision = "c8c5d7d4a4f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "crew_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("applicant_user_id", sa.Integer(), nullable=False),
        sa.Column("crew_id", sa.Integer(), nullable=True),
        sa.Column("proposed_name", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("activity_type", sa.String(length=20), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("meeting_point_name", sa.String(length=180), nullable=False),
        sa.Column("meeting_latitude", sa.Float(), nullable=False),
        sa.Column("meeting_longitude", sa.Float(), nullable=False),
        sa.Column("locality", sa.String(length=120), nullable=False),
        sa.Column("id_number", sa.String(length=80), nullable=False),
        sa.Column("selfie_filename", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["applicant_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["crew_id"], ["crews.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crew_applications_status", "crew_applications", ["status"])
    op.create_index("ix_crew_applications_applicant", "crew_applications", ["applicant_user_id"])


def downgrade():
    op.drop_index("ix_crew_applications_applicant", table_name="crew_applications")
    op.drop_index("ix_crew_applications_status", table_name="crew_applications")
    op.drop_table("crew_applications")
