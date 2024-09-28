"""Create all tables

Revision ID: d2886bdea872
Revises: da7e9b897343
Create Date: 2024-09-28 10:01:31.638988

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd2886bdea872'
down_revision = 'da7e9b897343'
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
