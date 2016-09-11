"""github oauth

Revision ID: b0a35e1fc164
Revises: 64f717aa0b00
Create Date: 2016-09-11 18:32:07.347241

"""

# revision identifiers, used by Alembic.
revision = 'b0a35e1fc164'
down_revision = '64f717aa0b00'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('oauth_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_oauth_type'))
    )
    op.create_table('oauth',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=True),
    sa.Column('local_uid', sa.Integer(), nullable=True),
    sa.Column('remote_uid', sa.Integer(), nullable=True),
    sa.Column('access_token', sa.String(length=400), nullable=True),
    sa.ForeignKeyConstraint(['local_uid'], ['users.id'], name=op.f('fk_oauth_local_uid_users')),
    sa.ForeignKeyConstraint(['type_id'], ['oauth_type.id'], name=op.f('fk_oauth_type_id_oauth_type')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_oauth')),
    sa.UniqueConstraint('access_token', name=op.f('uq_oauth_access_token'))
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('oauth')
    op.drop_table('oauth_type')
    ### end Alembic commands ###
