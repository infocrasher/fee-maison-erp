"""
Formulaires pour la gestion des 4 stocks et transferts
Module: app/stock/forms.py
Auteur: ERP Fée Maison
"""

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, TextAreaField, FieldList, FormField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product, User
from .models import StockLocationType

# Factory pour lister tous les produits
def all_product_query_factory():
    return Product.query.order_by(Product.name)

# Factory pour lister les produits actifs avec stock
def active_products_with_stock():
    return Product.query.filter(Product.quantity_in_stock > 0).order_by(Product.name)

# Factory pour lister tous les utilisateurs
def all_users_query_factory():
    return User.query.filter_by(role='admin').order_by(User.username)

# ==================== FORMULAIRES EXISTANTS CONSERVÉS ====================

class StockAdjustmentForm(FlaskForm):
    """Formulaire d'ajustement de stock (ancien - conservé pour compatibilité)"""
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    quantity = FloatField('Changement de quantité (+/-)', validators=[DataRequired()])
    reason = StringField('Raison', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Ajuster le stock')

class QuickStockEntryForm(FlaskForm):
    """Formulaire de réception rapide (étendu avec localisation)"""
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    quantity_received = FloatField('Quantité reçue', validators=[DataRequired(), NumberRange(min=0.01)])
    location_type = SelectField('Localisation', choices=[
        ('ingredients_magasin', 'Stock Magasin (Réserve)'),
        ('ingredients_local', 'Stock Local (Production)'),
        ('comptoir', 'Stock Comptoir (Vitrine)'),
        ('consommables', 'Stock Consommables (Emballages)')
    ], validators=[DataRequired()])
    reason = StringField('Raison/Référence', validators=[Optional(), Length(max=255)], 
                        render_kw={"placeholder": "Ex: Livraison fournisseur, Bon n°..."})
    submit = SubmitField('Ajouter au stock')

# ==================== NOUVEAUX FORMULAIRES POUR 4 STOCKS ====================

class MultiLocationAdjustmentForm(FlaskForm):
    """Formulaire d'ajustement avec sélection de localisation"""
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    location_type = SelectField('Localisation', choices=[
        ('comptoir', 'Stock Comptoir'),
        ('ingredients_local', 'Stock Local Production'),
        ('ingredients_magasin', 'Stock Magasin'),
        ('consommables', 'Stock Consommables')
    ], validators=[DataRequired()])
    quantity = FloatField('Changement de quantité (+/-)', validators=[DataRequired()], 
                         render_kw={"placeholder": "Nombre positif ou négatif"})
    reason = StringField('Raison de l\'ajustement', validators=[DataRequired(), Length(min=3, max=255)],
                        render_kw={"placeholder": "Ex: Inventaire, Perte, Casse..."})
    submit = SubmitField('Ajuster le stock')
    
    def validate_quantity(self, field):
        """Validation personnalisée pour empêcher les ajustements trop importants"""
        if abs(field.data) > 1000:
            raise ValidationError('L\'ajustement ne peut pas dépasser 1000 unités.')

class StockTransferLineForm(FlaskForm):
    """Formulaire pour une ligne de transfert"""
    product_id = IntegerField('Produit ID', validators=[Optional()])
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=True)
    quantity_requested = FloatField('Quantité', validators=[Optional(), NumberRange(min=0.01)])
    notes = StringField('Notes', validators=[Optional(), Length(max=255)])

class StockTransferForm(FlaskForm):
    """Formulaire de création de transfert entre stocks"""
    source_location = SelectField('Stock Source', choices=[
        ('ingredients_magasin', 'Stock Magasin → Stock Local'),
        ('ingredients_local', 'Stock Local → Stock Magasin'),
        ('comptoir', 'Stock Comptoir → Stock Local'),
        ('ingredients_local', 'Stock Local → Stock Comptoir')
    ], validators=[DataRequired()])
    
    destination_location = SelectField('Stock Destination', choices=[
        ('ingredients_local', 'Stock Local (Production)'),
        ('ingredients_magasin', 'Stock Magasin (Réserve)'),
        ('comptoir', 'Stock Comptoir (Vitrine)'),
        ('consommables', 'Stock Consommables')
    ], validators=[DataRequired()])
    
    reason = StringField('Motif du transfert', validators=[DataRequired(), Length(min=5, max=255)],
                        render_kw={"placeholder": "Ex: Réapprovisionnement production, Surplus..."})
    
    priority = SelectField('Priorité', choices=[
        ('low', 'Faible'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente')
    ], default='normal', validators=[DataRequired()])
    
    notes = TextAreaField('Notes complémentaires', validators=[Optional(), Length(max=500)],
                         render_kw={"rows": 3, "placeholder": "Informations supplémentaires..."})
    
    # Lignes de transfert (dynamiques)
    transfer_lines = FieldList(FormField(StockTransferLineForm), min_entries=1, max_entries=20)
    
    submit = SubmitField('Créer le transfert')
    
    def validate_source_location(self, field):
        """Validation pour éviter les transferts vers la même localisation"""
        if field.data == self.destination_location.data:
            raise ValidationError('La localisation source et destination ne peuvent pas être identiques.')
    
    def validate_transfer_lines(self, field):
        """Validation pour s'assurer qu'au moins une ligne est remplie"""
        valid_lines = 0
        for line in field.data:
            if line.get('product_id') and line.get('quantity_requested', 0) > 0:
                valid_lines += 1
        
        if valid_lines == 0:
            raise ValidationError('Au moins une ligne de transfert doit être remplie.')

class BulkStockUpdateForm(FlaskForm):
    """Formulaire de mise à jour en masse des stocks"""
    location_type = SelectField('Localisation cible', choices=[
        ('comptoir', 'Stock Comptoir'),
        ('ingredients_local', 'Stock Local Production'),
        ('ingredients_magasin', 'Stock Magasin'),
        ('consommables', 'Stock Consommables')
    ], validators=[DataRequired()])
    
    operation_type = SelectField('Type d\'opération', choices=[
        ('set_zero', 'Remettre à zéro'),
        ('multiply', 'Multiplier par'),
        ('add', 'Ajouter'),
        ('subtract', 'Soustraire')
    ], validators=[DataRequired()])
    
    value = FloatField('Valeur', validators=[Optional(), NumberRange(min=0)],
                      render_kw={"placeholder": "Valeur pour l'opération"})
    
    reason = StringField('Raison de l\'opération', validators=[DataRequired(), Length(min=5, max=255)],
                        render_kw={"placeholder": "Ex: Inventaire général, Réinitialisation..."})
    
    confirm = StringField('Tapez "CONFIRMER" pour valider', validators=[DataRequired()],
                         render_kw={"placeholder": "CONFIRMER"})
    
    submit = SubmitField('Exécuter l\'opération en masse')
    
    def validate_confirm(self, field):
        """Validation de confirmation pour les opérations en masse"""
        if field.data.upper() != 'CONFIRMER':
            raise ValidationError('Vous devez taper "CONFIRMER" pour valider cette opération.')
    
    def validate_value(self, field):
        """Validation de la valeur selon le type d'opération"""
        if self.operation_type.data in ['multiply', 'add', 'subtract'] and not field.data:
            raise ValidationError('Une valeur est requise pour cette opération.')

class StockSearchForm(FlaskForm):
    """Formulaire de recherche dans les stocks"""
    search_term = StringField('Rechercher un produit', validators=[Optional(), Length(max=100)],
                             render_kw={"placeholder": "Nom, référence ou catégorie..."})
    
    location_filter = SelectField('Filtrer par localisation', choices=[
        ('all', 'Toutes les localisations'),
        ('comptoir', 'Stock Comptoir'),
        ('ingredients_local', 'Stock Local'),
        ('ingredients_magasin', 'Stock Magasin'),
        ('consommables', 'Consommables')
    ], default='all')
    
    stock_status = SelectField('Statut du stock', choices=[
        ('all', 'Tous les statuts'),
        ('in_stock', 'En stock'),
        ('low_stock', 'Stock faible'),
        ('out_of_stock', 'Rupture'),
        ('overstocked', 'Surplus')
    ], default='all')
    
    submit = SubmitField('Rechercher')

class StockAlertForm(FlaskForm):
    """Formulaire de configuration des alertes de stock"""
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    
    seuil_comptoir = FloatField('Seuil alerte Comptoir', validators=[Optional(), NumberRange(min=0)],
                               render_kw={"placeholder": "Quantité minimale"})
    
    seuil_local = FloatField('Seuil alerte Local', validators=[Optional(), NumberRange(min=0)],
                            render_kw={"placeholder": "Quantité minimale"})
    
    seuil_magasin = FloatField('Seuil alerte Magasin', validators=[Optional(), NumberRange(min=0)],
                              render_kw={"placeholder": "Quantité minimale"})
    
    seuil_consommables = FloatField('Seuil alerte Consommables', validators=[Optional(), NumberRange(min=0)],
                                   render_kw={"placeholder": "Quantité minimale"})
    
    submit = SubmitField('Configurer les alertes')
