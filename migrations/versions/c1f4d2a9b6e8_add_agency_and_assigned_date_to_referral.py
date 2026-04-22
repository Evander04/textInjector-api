"""add agency and assigned date to referral

Revision ID: c1f4d2a9b6e8
Revises: b7c3a91d4e2f
Create Date: 2026-04-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1f4d2a9b6e8'
down_revision = 'b7c3a91d4e2f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('referral', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agency', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('assigned_date', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('referral', schema=None) as batch_op:
        batch_op.drop_column('assigned_date')
        batch_op.drop_column('agency')
