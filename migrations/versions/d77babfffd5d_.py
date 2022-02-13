"""empty message

Revision ID: d77babfffd5d
Revises: 2e797074a63f
Create Date: 2022-02-03 11:15:06.066943

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd77babfffd5d'
down_revision = '2e797074a63f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sentence', sa.Column('source', sa.String(length=100), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sentence', 'source')
    # ### end Alembic commands ###