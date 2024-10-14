"""Recreate user table

Revision ID: ca89dfa48e7e
Revises: 9a86d70af627
Create Date: 2024-10-14 01:26:48.317484
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# Revision identifiers, used by Alembic.
revision = 'ca89dfa48e7e'
down_revision = '9a86d70af627'
branch_labels = None
depends_on = None

def upgrade():
    # Get the current database connection
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)

    # Create the 'item' table if it doesn't already exist
    if 'item' not in inspector.get_table_names():
        op.create_table(
            'item',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('par', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    # Create the 'user' table if it doesn't already exist
    if 'user' not in inspector.get_table_names():
        op.create_table(
            'user',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=150), nullable=False),
            sa.Column('password_hash', sa.String(length=256), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username')
        )

    # Create the 'stock_record' table if it doesn't already exist
    if 'stock_record' not in inspector.get_table_names():
        op.create_table(
            'stock_record',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('item_id', sa.Integer(), nullable=False),
            sa.Column('current_stock', sa.Integer(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['item_id'], ['item.id']),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade():
    # Drop the tables in reverse order of creation
    op.drop_table('stock_record')
    op.drop_table('user')
    op.drop_table('item')
