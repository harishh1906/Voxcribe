"""initial migration – create transcriptions table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transcriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False, server_default="Untitled Recording"),
        sa.Column("transcription_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("language_detected", sa.String(50), nullable=True),
        sa.Column("duration_seconds", sa.Float(), server_default="0"),
        sa.Column("word_count", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(20), server_default="completed"),
        sa.Column("audio_file_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("transcriptions")
