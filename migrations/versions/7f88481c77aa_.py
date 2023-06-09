"""empty message

Revision ID: 7f88481c77aa
Revises: 67ddd3ada910
Create Date: 2023-04-01 19:33:25.829750

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f88481c77aa'
down_revision = '67ddd3ada910'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('address', sa.String(length=20), nullable=False))
        batch_op.create_unique_constraint(None, ['address'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('address')

    # ### end Alembic commands ###
