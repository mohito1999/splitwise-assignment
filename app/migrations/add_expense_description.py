"""add expense description and timestamp

Revision ID: add_expense_description
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add description column
    op.add_column('expenses', sa.Column('description', sa.String(), nullable=True))
    # Add created_at column with default timestamp
    op.add_column('expenses', sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
    
    # Update existing rows to have a default description
    op.execute("UPDATE expenses SET description = 'Expense' WHERE description IS NULL")
    
def downgrade():
    op.drop_column('expenses', 'created_at')
    op.drop_column('expenses', 'description') 