"""rpm voting

Revision ID: 79c08935d93e
Revises: 329a35dc3698
Create Date: 2016-09-19 21:22:45.978798

"""

# revision identifiers, used by Alembic.
revision = '79c08935d93e'
down_revision = '329a35dc3698'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('releases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_releases'))
    )
    op.create_table('packages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=True),
    sa.Column('pkgnames', sa.Text(), nullable=True),
    sa.Column('task_id', sa.String(length=100), nullable=True),
    sa.Column('release_id', sa.Integer(), nullable=True),
    sa.Column('karma', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=10), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('deadline', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['release_id'], ['releases.id'], name=op.f('fk_packages_release_id_releases')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_packages')),
    sa.UniqueConstraint('task_id', name=op.f('uq_packages_task_id'))
    )
    with op.batch_alter_table(u'comments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('package_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_comments_package_id_packages'), 'packages', ['package_id'], ['id'])

    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(u'comments', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_comments_package_id_packages'), type_='foreignkey')
        batch_op.drop_column('package_id')

    op.drop_table('packages')
    op.drop_table('releases')
    ### end Alembic commands ###