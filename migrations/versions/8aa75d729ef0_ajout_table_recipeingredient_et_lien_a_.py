"""Ajout table RecipeIngredient et lien a Recipe

Revision ID: 8aa75d729ef0
Revises: adeaabdabae2
Create Date: 2025-06-24 01:12:28.019016

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8aa75d729ef0'
down_revision = 'adeaabdabae2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('recipe_ingredients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recipe_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity_needed', sa.Numeric(precision=10, scale=3), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('notes', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('recipe_ingredients')
    # ### end Alembic commands ###
