"""add receipt amounts to students

Revision ID: 9f2c6d4a1b7e
Revises: 3a79eaa0e315
Create Date: 2026-03-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9f2c6d4a1b7e'
down_revision = '3a79eaa0e315'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('receiptAmounts', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_column('receiptAmounts')
