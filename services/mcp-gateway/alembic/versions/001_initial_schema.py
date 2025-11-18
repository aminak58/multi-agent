"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-11-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""

    # Orders table
    op.create_table(
        'orders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('request_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('agent', sa.String(50), nullable=False),
        sa.Column('pair', sa.String(20), nullable=False),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('qty', sa.Numeric(20, 8), nullable=False),
        sa.Column('type', sa.String(10), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('price', sa.Numeric(20, 8), nullable=True),
        sa.Column('filled_qty', sa.Numeric(20, 8), nullable=True),
        sa.Column('avg_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('meta', JSONB, nullable=True),
    )

    # Create indexes for orders
    op.create_index('ix_orders_request_id', 'orders', ['request_id'])
    op.create_index('ix_orders_agent', 'orders', ['agent'])
    op.create_index('ix_orders_pair', 'orders', ['pair'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])

    # Decisions table
    op.create_table(
        'decisions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('request_id', UUID(as_uuid=True), nullable=False),
        sa.Column('agent', sa.String(50), nullable=False),
        sa.Column('pair', sa.String(20), nullable=False),
        sa.Column('action', sa.String(10), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('llm_used', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('meta', JSONB, nullable=True),
    )

    # Create indexes for decisions
    op.create_index('ix_decisions_request_id', 'decisions', ['request_id'])
    op.create_index('ix_decisions_agent', 'decisions', ['agent'])
    op.create_index('ix_decisions_pair', 'decisions', ['pair'])
    op.create_index('ix_decisions_created_at', 'decisions', ['created_at'])
    op.create_index('ix_decisions_llm_used', 'decisions', ['llm_used'])

    # LLM logs table
    op.create_table(
        'llm_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('request_id', UUID(as_uuid=True), nullable=False),
        sa.Column('input_hash', sa.String(64), nullable=False),
        sa.Column('prompt', sa.Text, nullable=False),
        sa.Column('response', sa.Text, nullable=True),
        sa.Column('model', sa.String(50), nullable=False),
        sa.Column('temperature', sa.Numeric(3, 2), nullable=True),
        sa.Column('tokens_in', sa.Integer, nullable=True),
        sa.Column('tokens_out', sa.Integer, nullable=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('meta', JSONB, nullable=True),
    )

    # Create indexes for llm_logs
    op.create_index('ix_llm_logs_request_id', 'llm_logs', ['request_id'])
    op.create_index('ix_llm_logs_input_hash', 'llm_logs', ['input_hash'])
    op.create_index('ix_llm_logs_created_at', 'llm_logs', ['created_at'])
    op.create_index('ix_llm_logs_status', 'llm_logs', ['status'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('llm_logs')
    op.drop_table('decisions')
    op.drop_table('orders')
