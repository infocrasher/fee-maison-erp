"""
Formulaires pour la gestion des achats fournisseurs
Module: app/purchases/forms.py
Auteur: ERP Fée Maison
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField, HiddenField, FieldList, FormField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from decimal import Decimal
from models import Product
from .models import PurchaseStatus, PurchaseUrgency

# Factory pour lister tous les produits
def all_products_query():
    return Product.query.order_by(Product.name)

# Factory pour lister les produits ingrédients et consommables
def purchasable_products_query():
    return Product.query.filter(
        Product.product_type.in_(['ingredient', 'consommable'])
    ).order_by(Product.name)

class PurchaseItemForm(FlaskForm):
    """Formulaire pour une ligne d'article d'achat"""
    product_id = IntegerField('Produit ID', validators=[Optional()])
    product = QuerySelectField('Produit', query_factory=purchasable_products_query, get_label='name', allow_blank=True)
    quantity_ordered = FloatField('Quantité', validators=[Optional(), NumberRange(min=0.01)])
    unit_price = FloatField('Prix unitaire (DA)', validators=[Optional(), NumberRange(min=0.01)])
    discount_percentage = FloatField('Remise (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    
    stock_location = SelectField('Stock destination', choices=[
        ('ingredients_magasin', 'Stock Magasin (Par défaut)'),
        ('ingredients_local', 'Stock Local Production'),
        ('comptoir', 'Stock Comptoir'),
        ('consommables', 'Stock Consommables')
    ], default='ingredients_magasin')
    
    description_override = StringField('Description spécifique', validators=[Optional(), Length(max=255)])
    supplier_reference = StringField('Référence fournisseur', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])

class PurchaseForm(FlaskForm):
    """Formulaire principal de création/modification d'achat"""
    
    # Informations fournisseur
    supplier_name = StringField('Nom du fournisseur', validators=[DataRequired(), Length(min=2, max=200)])
    supplier_contact = StringField('Personne de contact', validators=[Optional(), Length(max=100)])
    supplier_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    supplier_email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    supplier_address = TextAreaField('Adresse', validators=[Optional(), Length(max=500)])
    
    # Dates et urgence
    expected_delivery_date = DateTimeLocalField('Date de livraison prévue', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    urgency = SelectField('Urgence', choices=[
        (PurchaseUrgency.NORMAL.value, 'Normale'),
        (PurchaseUrgency.LOW.value, 'Faible'),
        (PurchaseUrgency.HIGH.value, 'Haute'),
        (PurchaseUrgency.URGENT.value, 'Urgente')
    ], default=PurchaseUrgency.NORMAL.value)
    
    # Stock destination par défaut
    default_stock_location = SelectField('Stock destination par défaut', choices=[
        ('ingredients_magasin', 'Stock Magasin'),
        ('ingredients_local', 'Stock Local Production'),
        ('comptoir', 'Stock Comptoir'),
        ('consommables', 'Stock Consommables')
    ], default='ingredients_magasin')
    
    # Conditions commerciales
    payment_terms = StringField('Conditions de paiement', validators=[Optional(), Length(max=100)], 
                                render_kw={"placeholder": "Ex: 30 jours net, Comptant..."})
    shipping_cost = FloatField('Frais de port (DA)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    tax_amount = FloatField('Montant TVA (DA)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Notes
    notes = TextAreaField('Notes générales', validators=[Optional(), Length(max=1000)], 
                         render_kw={"rows": 3, "placeholder": "Informations pour le fournisseur..."})
    internal_notes = TextAreaField('Notes internes', validators=[Optional(), Length(max=1000)],
                                  render_kw={"rows": 3, "placeholder": "Notes internes non visibles du fournisseur..."})
    terms_conditions = TextAreaField('Conditions particulières', validators=[Optional(), Length(max=1000)],
                                    render_kw={"rows": 3, "placeholder": "Conditions spéciales..."})
    
    # Articles (géré dynamiquement)
    items = FieldList(FormField(PurchaseItemForm), min_entries=1, max_entries=50)
    
    # Actions
    submit = SubmitField('Enregistrer le bon d\'achat')
    submit_and_request = SubmitField('Enregistrer et Demander l\'approbation')
    
    def validate_supplier_name(self, field):
        """Validation du nom fournisseur"""
        if len(field.data.strip()) < 2:
            raise ValidationError('Le nom du fournisseur doit contenir au moins 2 caractères.')
    
    def validate_items(self, field):
        """Validation des lignes d'articles"""
        valid_items = 0
        for item in field.data:
            if item.get('product_id') and item.get('quantity_ordered', 0) > 0 and item.get('unit_price', 0) > 0:
                valid_items += 1
        
        if valid_items == 0:
            raise ValidationError('Au moins un article avec quantité et prix doit être spécifié.')
    
    def validate_expected_delivery_date(self, field):
        """Validation de la date de livraison"""
        if field.data:
            from datetime import datetime
            if field.data < datetime.now():
                raise ValidationError('La date de livraison ne peut pas être dans le passé.')

class PurchaseApprovalForm(FlaskForm):
    """Formulaire d'approbation d'un bon d'achat"""
    approval_notes = TextAreaField('Notes d\'approbation', validators=[Optional(), Length(max=500)],
                                  render_kw={"rows": 3, "placeholder": "Commentaires sur l'approbation..."})
    
    # Modifications autorisées lors de l'approbation
    shipping_cost = FloatField('Frais de port (DA)', validators=[Optional(), NumberRange(min=0)])
    tax_amount = FloatField('Montant TVA (DA)', validators=[Optional(), NumberRange(min=0)])
    expected_delivery_date = DateTimeLocalField('Date de livraison prévue', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    
    approve = SubmitField('Approuver')
    reject = SubmitField('Rejeter')

class PurchaseReceiptForm(FlaskForm):
    """Formulaire de réception de marchandises"""
    receipt_notes = TextAreaField('Notes de réception', validators=[Optional(), Length(max=500)],
                                 render_kw={"rows": 3, "placeholder": "État des marchandises, problèmes éventuels..."})
    
    # Champs pour chaque ligne (généré dynamiquement)
    partial_receipt = SubmitField('Réception partielle')
    complete_receipt = SubmitField('Réception complète')

class PurchaseReceiptItemForm(FlaskForm):
    """Formulaire pour la réception d'un article spécifique"""
    item_id = HiddenField('Article ID')
    quantity_to_receive = FloatField('Quantité à recevoir', validators=[DataRequired(), NumberRange(min=0.01)])
    stock_location = SelectField('Stock destination', choices=[
        ('ingredients_magasin', 'Stock Magasin'),
        ('ingredients_local', 'Stock Local Production'),
        ('comptoir', 'Stock Comptoir'),
        ('consommables', 'Stock Consommables')
    ])
    notes = StringField('Notes', validators=[Optional(), Length(max=255)])

class PurchaseSearchForm(FlaskForm):
    """Formulaire de recherche dans les achats"""
    search_term = StringField('Rechercher', validators=[Optional(), Length(max=100)],
                             render_kw={"placeholder": "Référence, fournisseur, produit..."})
    
    status_filter = SelectField('Statut', choices=[
        ('all', 'Tous les statuts'),
        (PurchaseStatus.DRAFT.value, 'Brouillon'),
        (PurchaseStatus.REQUESTED.value, 'Demandé'),
        (PurchaseStatus.APPROVED.value, 'Approuvé'),
        (PurchaseStatus.ORDERED.value, 'Commandé'),
        (PurchaseStatus.PARTIALLY_RECEIVED.value, 'Partiellement reçu'),
        (PurchaseStatus.RECEIVED.value, 'Reçu'),
        (PurchaseStatus.INVOICED.value, 'Facturé'),
        (PurchaseStatus.CANCELLED.value, 'Annulé')
    ], default='all')
    
    urgency_filter = SelectField('Urgence', choices=[
        ('all', 'Toutes les urgences'),
        (PurchaseUrgency.LOW.value, 'Faible'),
        (PurchaseUrgency.NORMAL.value, 'Normale'),
        (PurchaseUrgency.HIGH.value, 'Haute'),
        (PurchaseUrgency.URGENT.value, 'Urgente')
    ], default='all')
    
    supplier_filter = StringField('Fournisseur', validators=[Optional(), Length(max=100)],
                                 render_kw={"placeholder": "Nom du fournisseur..."})
    
    submit = SubmitField('Rechercher')

class QuickPurchaseForm(FlaskForm):
    """Formulaire d'achat rapide pour un produit spécifique"""
    product = QuerySelectField('Produit', query_factory=purchasable_products_query, get_label='name', allow_blank=False)
    quantity = FloatField('Quantité', validators=[DataRequired(), NumberRange(min=0.01)])
    unit_price = FloatField('Prix unitaire (DA)', validators=[DataRequired(), NumberRange(min=0.01)])
    
    supplier_name = StringField('Fournisseur', validators=[DataRequired(), Length(min=2, max=200)])
    supplier_phone = StringField('Téléphone fournisseur', validators=[Optional(), Length(max=20)])
    
    stock_location = SelectField('Stock destination', choices=[
        ('ingredients_magasin', 'Stock Magasin'),
        ('ingredients_local', 'Stock Local Production'),
        ('comptoir', 'Stock Comptoir'),
        ('consommables', 'Stock Consommables')
    ], default='ingredients_magasin')
    
    urgency = SelectField('Urgence', choices=[
        (PurchaseUrgency.NORMAL.value, 'Normale'),
        (PurchaseUrgency.HIGH.value, 'Haute'),
        (PurchaseUrgency.URGENT.value, 'Urgente')
    ], default=PurchaseUrgency.NORMAL.value)
    
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)],
                         render_kw={"rows": 2, "placeholder": "Informations complémentaires..."})
    
    submit = SubmitField('Créer l\'achat rapide')

class SupplierForm(FlaskForm):
    """Formulaire de gestion des informations fournisseur"""
    name = StringField('Nom du fournisseur', validators=[DataRequired(), Length(min=2, max=200)])
    contact_person = StringField('Personne de contact', validators=[Optional(), Length(max=100)])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Adresse complète', validators=[Optional(), Length(max=500)],
                           render_kw={"rows": 3})
    
    default_payment_terms = StringField('Conditions de paiement par défaut', validators=[Optional(), Length(max=100)],
                                       render_kw={"placeholder": "Ex: 30 jours net"})
    
    notes = TextAreaField('Notes sur le fournisseur', validators=[Optional(), Length(max=1000)],
                         render_kw={"rows": 3, "placeholder": "Historique, particularités..."})
    
    submit = SubmitField('Enregistrer le fournisseur')

class BulkPurchaseStatusForm(FlaskForm):
    """Formulaire de modification en masse du statut d'achats"""
    new_status = SelectField('Nouveau statut', choices=[
        (PurchaseStatus.ORDERED.value, 'Marquer comme Commandé'),
        (PurchaseStatus.CANCELLED.value, 'Annuler'),
        (PurchaseStatus.APPROVED.value, 'Approuver')
    ], validators=[DataRequired()])
    
    reason = TextAreaField('Motif de la modification', validators=[DataRequired(), Length(min=5, max=500)],
                          render_kw={"rows": 3, "placeholder": "Expliquez la raison de cette modification en masse..."})
    
    confirm = StringField('Tapez "CONFIRMER" pour valider', validators=[DataRequired()],
                         render_kw={"placeholder": "CONFIRMER"})
    
    submit = SubmitField('Appliquer à la sélection')
    
    def validate_confirm(self, field):
        """Validation de confirmation"""
        if field.data.upper() != 'CONFIRMER':
            raise ValidationError('Vous devez taper "CONFIRMER" pour valider cette opération.')
