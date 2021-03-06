"""user score field

Revision ID: 3a4b44ba89c7
Revises: c0e1a2f849a4
Create Date: 2020-10-03 17:59:55.678120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a4b44ba89c7'
down_revision = 'c0e1a2f849a4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('score', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'score')
    # ### end Alembic commands ###
