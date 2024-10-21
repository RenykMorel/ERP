"""empty message

Revision ID: cd12b5839861
Revises: 65685ab2b093
Create Date: 2024-09-21 23:05:50.307574

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cd12b5839861'
down_revision = '65685ab2b093'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('historial')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('historial',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('accion', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('fecha', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='historial_pkey')
    )
    # ### end Alembic commands ###