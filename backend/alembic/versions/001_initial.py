"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Episodes table
    op.create_table(
        'episodes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('guest', sa.String(255), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('youtube_url', sa.String(500), nullable=True),
        sa.Column('video_id', sa.String(50), nullable=True),
        sa.Column('publish_date', sa.Date, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('duration_seconds', sa.BigInteger, nullable=True),
        sa.Column('duration', sa.String(50), nullable=True),
        sa.Column('view_count', sa.BigInteger, nullable=True),
        sa.Column('channel', sa.String(255), nullable=True),
        sa.Column('transcript_content', sa.Text, nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_episodes_publish_date', 'episodes', ['publish_date'])
    op.execute('CREATE INDEX ix_episodes_embedding ON episodes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')

    # Chat sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata_', JSONB, nullable=False, server_default='{}'),
        sa.Column('sources', JSONB, nullable=False, server_default='[]'),
        sa.Column('artifact_ids', ARRAY(UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_messages_session_id', 'messages', ['session_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])

    # Artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_artifacts_session_id', 'artifacts', ['session_id'])
    op.create_index('ix_artifacts_message_id', 'artifacts', ['message_id'])


def downgrade() -> None:
    op.drop_index('ix_artifacts_message_id', table_name='artifacts')
    op.drop_index('ix_artifacts_session_id', table_name='artifacts')
    op.drop_table('artifacts')

    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_session_id', table_name='messages')
    op.drop_table('messages')

    op.drop_table('chat_sessions')

    op.execute('DROP INDEX IF EXISTS ix_episodes_embedding')
    op.drop_index('ix_episodes_publish_date', table_name='episodes')
    op.drop_table('episodes')

    op.execute('DROP EXTENSION IF EXISTS vector')