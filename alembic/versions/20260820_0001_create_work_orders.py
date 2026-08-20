"""create work orders table

Revision ID: 20260820_0001
Revises:
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("assignee", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_work_orders_id"), "work_orders", ["id"], unique=False)
    op.create_index(op.f("ix_work_orders_title"), "work_orders", ["title"], unique=False)
    op.create_index(op.f("ix_work_orders_priority"), "work_orders", ["priority"], unique=False)
    op.create_index(op.f("ix_work_orders_status"), "work_orders", ["status"], unique=False)
    op.create_index(op.f("ix_work_orders_assignee"), "work_orders", ["assignee"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_work_orders_assignee"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_status"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_priority"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_title"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_id"), table_name="work_orders")
    op.drop_table("work_orders")
