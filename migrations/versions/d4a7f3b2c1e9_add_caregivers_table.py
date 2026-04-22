"""add caregivers table

Revision ID: d4a7f3b2c1e9
Revises: c1f4d2a9b6e8
Create Date: 2026-04-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4a7f3b2c1e9'
down_revision = 'c1f4d2a9b6e8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'caregivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=300), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('registry_number', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=150), nullable=True),
        sa.Column('agency', sa.String(length=200), nullable=True),
        sa.Column('license', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('caregivers')
