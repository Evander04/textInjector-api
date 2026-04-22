"""add hcr fields to caregivers

Revision ID: f2c6d9a4b1e7
Revises: d4a7f3b2c1e9
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f2c6d9a4b1e7'
down_revision = 'd4a7f3b2c1e9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('caregivers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agencies', postgresql.ARRAY(sa.String()), nullable=True))
        batch_op.add_column(sa.Column('workStatus', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('queryStatus', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('workStartDate', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('benefitStatus', sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table('caregivers', schema=None) as batch_op:
        batch_op.drop_column('benefitStatus')
        batch_op.drop_column('workStartDate')
        batch_op.drop_column('queryStatus')
        batch_op.drop_column('workStatus')
        batch_op.drop_column('agencies')
