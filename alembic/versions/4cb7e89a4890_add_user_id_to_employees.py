"""add user_id to employees

Revision ID: 4cb7e89a4890
Revises: 9d455cc0cc25
Create Date: 2026-08-07 12:01:33.570109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cb7e89a4890'
down_revision: Union[str, Sequence[str], None] = '9d455cc0cc25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('employees', 
        sa.Column('user_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_employees_user_id', 
        'employees', 'users',
        ['user_id'], ['id']
    )

def downgrade() -> None:
    op.drop_constraint('fk_employees_user_id', 'employees', type_='foreignkey')
    op.drop_column('employees', 'user_id')
