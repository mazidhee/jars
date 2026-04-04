"""create_market_trades_hypertable

Revision ID: a5d6e7f8g9h0
Revises: 04858647df73
Create Date: 2026-03-24 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5d6e7f8g9h0'
down_revision: Union[str, Sequence[str], None] = '04858647df73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable TimescaleDB extension
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;')

    # 2. Create the market_trades table
    # Note: TimescaleDB requires the partitioning column (timestamp) to be part of the Primary Key
    op.create_table('market_trades',
        sa.Column('trade_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('qty', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('trade_id', 'timestamp')
    )

    # 3. Convert standard table to a TimescaleDB hypertable chunked by 1 day
    op.execute("SELECT create_hypertable('market_trades', 'timestamp', chunk_time_interval => INTERVAL '1 day');")


def downgrade() -> None:
    op.drop_table('market_trades')
