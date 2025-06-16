"""Add 4-stock management system to products

Revision ID: 08ee5551824b
Revises: 9a043041c254
Create Date: 2025-06-16 02:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '08ee5551824b'
down_revision = '9a043041c254'
branch_labels = None
depends_on = None

def upgrade():
    # === EXTENSION MODÈLE PRODUCT ===
    
    # Ajout des 4 champs de stock avec valeurs par défaut
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock_comptoir', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('stock_ingredients_local', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('stock_ingredients_magasin', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('stock_consommables', sa.Float(), nullable=True))
        
        # Ajout des seuils minimum
        batch_op.add_column(sa.Column('seuil_min_comptoir', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('seuil_min_ingredients_local', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('seuil_min_ingredients_magasin', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('seuil_min_consommables', sa.Float(), nullable=True))
        
        # Date de dernière mise à jour
        batch_op.add_column(sa.Column('last_stock_update', sa.DateTime(), nullable=True))
    
    # Mise à jour des valeurs NULL vers 0.0 pour les nouveaux champs de stock
    op.execute("UPDATE products SET stock_comptoir = 0.0 WHERE stock_comptoir IS NULL")
    op.execute("UPDATE products SET stock_ingredients_local = 0.0 WHERE stock_ingredients_local IS NULL")
    op.execute("UPDATE products SET stock_ingredients_magasin = 0.0 WHERE stock_ingredients_magasin IS NULL")
    op.execute("UPDATE products SET stock_consommables = 0.0 WHERE stock_consommables IS NULL")
    op.execute("UPDATE products SET last_stock_update = NOW() WHERE last_stock_update IS NULL")
    
    # Mise à jour des seuils minimum vers 0.0
    op.execute("UPDATE products SET seuil_min_comptoir = 0.0 WHERE seuil_min_comptoir IS NULL")
    op.execute("UPDATE products SET seuil_min_ingredients_local = 0.0 WHERE seuil_min_ingredients_local IS NULL")
    op.execute("UPDATE products SET seuil_min_ingredients_magasin = 0.0 WHERE seuil_min_ingredients_magasin IS NULL")
    op.execute("UPDATE products SET seuil_min_consommables = 0.0 WHERE seuil_min_consommables IS NULL")
    
    # Rendre les colonnes de stock NOT NULL après mise à jour
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column('stock_comptoir', nullable=False)
        batch_op.alter_column('stock_ingredients_local', nullable=False)
        batch_op.alter_column('stock_ingredients_magasin', nullable=False)
        batch_op.alter_column('stock_consommables', nullable=False)

def downgrade():
    # === SUPPRESSION DES COLONNES PRODUCT ===
    
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('last_stock_update')
        batch_op.drop_column('seuil_min_consommables')
        batch_op.drop_column('seuil_min_ingredients_magasin')
        batch_op.drop_column('seuil_min_ingredients_local')
        batch_op.drop_column('seuil_min_comptoir')
        batch_op.drop_column('stock_consommables')
        batch_op.drop_column('stock_ingredients_magasin')
        batch_op.drop_column('stock_ingredients_local')
        batch_op.drop_column('stock_comptoir')
