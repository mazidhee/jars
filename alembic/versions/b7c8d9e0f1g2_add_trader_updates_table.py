"""add_trader_updates_table

Revision ID: b7c8d9e0f1g2
Revises: a5d6e7f8g9h0
Create Date: 2026-04-04 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = 'b7c8d9e0f1g2'
down_revision: Union[str, Sequence[str], None] = 'a5d6e7f8g9h0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'update_visibility') THEN
                CREATE TYPE update_visibility AS ENUM ('public', 'subscribers_only');
            END IF;
        END $$;
    """)

    op.create_table('trader_updates',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('trader_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('visibility', sa.Enum('public', 'subscribers_only', name='update_visibility', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trader_id'], ['trader_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_trader_updates_trader_id', 'trader_updates', ['trader_id'])
    op.create_index('ix_trader_updates_created_at', 'trader_updates', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_trader_updates_created_at', table_name='trader_updates')
    op.drop_index('ix_trader_updates_trader_id', table_name='trader_updates')
    op.drop_table('trader_updates')
    sa.Enum(name='update_visibility').drop(op.get_bind(), checkfirst=True)
