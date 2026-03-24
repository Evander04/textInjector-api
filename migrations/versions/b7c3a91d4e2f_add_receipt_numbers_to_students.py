"""add receipt numbers to students

Revision ID: b7c3a91d4e2f
Revises: 9f2c6d4a1b7e
Create Date: 2026-03-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b7c3a91d4e2f'
down_revision = '9f2c6d4a1b7e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('receiptNumbers', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_column('receiptNumbers')
