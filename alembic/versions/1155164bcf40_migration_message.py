"""migration message

Revision ID: 1155164bcf40
Revises: 0c39d4b83886
Create Date: 2025-06-28 17:02:22.265090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1155164bcf40'
down_revision: Union[str, Sequence[str], None] = '0c39d4b83886'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task_message_association',
    sa.Column('task_id', sa.UUID(), nullable=False),
    sa.Column('message_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['message_id'], ['messages.message_id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id'], ),
    sa.PrimaryKeyConstraint('task_id', 'message_id')
    )
    op.drop_column('tasks', 'created_by_agent')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('created_by_agent', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_table('task_message_association')
    # ### end Alembic commands ###
