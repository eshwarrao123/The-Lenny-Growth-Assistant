"""Phase 2 Schema

Revision ID: 002_phase2_schema
Revises: 001_initial
Create Date: 2026-09-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_phase2_schema'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Drop existing tables to recreate based on Phase 2 (since Phase 1 was just foundation and no data)
    op.drop_table('artifacts', if_exists=True)
    op.drop_table('messages', if_exists=True)
    op.drop_table('chat_sessions', if_exists=True)
    op.drop_table('episodes', if_exists=True)
    # The previous migration might have different names or structure.
    
    # Recreate episodes
    op.create_table('episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('guest_name', sa.String(length=255), nullable=True),
        sa.Column('publish_date', sa.Date(), nullable=True),
        sa.Column('youtube_url', sa.String(length=500), nullable=True),
        sa.Column('video_id', sa.String(length=50), nullable=True),
        sa.Column('duration_seconds', sa.BigInteger(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id')
    )
    
    # Create transcript_chunks
    op.create_table('transcript_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('speaker', sa.String(length=255), nullable=True),
        sa.Column('start_time', sa.String(length=50), nullable=True),
        sa.Column('embedding', postgresql.VECTOR(dim=768), nullable=True),
        sa.Column('metadata_', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chunks_episode_id', 'transcript_chunks', ['episode_id'], unique=False)
    op.execute("CREATE INDEX ix_chunks_embedding ON transcript_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)")

    # Create chat_sessions
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create messages
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_session_id', 'messages', ['session_id'], unique=False)
    op.create_index('ix_messages_created_at', 'messages', ['created_at'], unique=False)

    # Create artifacts
    op.create_table('artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_artifacts_message_id', 'artifacts', ['message_id'], unique=False)
    op.create_index('ix_artifacts_session_id', 'artifacts', ['session_id'], unique=False)

def downgrade() -> None:
    pass
