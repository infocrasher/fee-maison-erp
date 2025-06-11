# --- START OF FILE forms.py ---

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField, TextAreaField, 
                     SelectField, FloatField, IntegerField, FieldList, FormField,
                     DateTimeField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField

from models import Category, Product, Recipe

# --- FACTORIES ---
def category_query_factory():
    return Category.query.order_by(Category.name)

def finished_product_query_factory():
    # Produits finis qui n'ont pas encore de recette associée
    return Product.query.filter_by(product_type='finished').filter(~Product.recipe_definition.has()).order_by(Product.name)
    
def finished_product_query_factory_for_orders():
    return Product.query.filter_by(product_type='finished').order_by(Product.name)

def ingredient_product_query_factory():
    return Product.query.filter_by(product_type='ingredient').order_by(Product.name)

def all_product_query_factory():
    return Product.query.order_by(Product.name)

# --- FORMS ---

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Connexion')

class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('Nouveau mot de passe', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Changer le mot de passe')

class CategoryForm(FlaskForm):
    name = StringField('Nom de la catégorie', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class ProductForm(FlaskForm):
    name = StringField('Nom du produit', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    sku = StringField('SKU / Référence', validators=[Optional(), Length(max=50)])
    product_type = SelectField('Type', choices=[('finished', 'Produit Fini'), ('ingredient', 'Ingrédient')], validators=[DataRequired()])
    unit = StringField('Unité (ex: kg, L, pièce)', validators=[DataRequired(), Length(max=20)])
    price = FloatField('Prix de vente (€)', validators=[Optional(), NumberRange(min=0)])
    cost_price = FloatField("Prix d'achat / Coût de revient (€)", validators=[Optional(), NumberRange(min=0)])
    quantity_in_stock = FloatField('Quantité en stock', default=0, validators=[DataRequired(), NumberRange(min=0)])
    category = QuerySelectField('Catégorie', query_factory=category_query_factory, get_label='name', allow_blank=False)
    submit = SubmitField('Enregistrer le produit')

class StockAdjustmentForm(FlaskForm):
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    quantity = FloatField('Changement de quantité (+/-)', validators=[DataRequired()])
    reason = StringField('Raison', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Ajuster le stock')

class QuickStockEntryForm(FlaskForm):
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    quantity_received = FloatField('Quantité reçue', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Ajouter au stock')

class OrderItemForm(FlaskForm):
    product = QuerySelectField('Produit', query_factory=finished_product_query_factory_for_orders, get_label='name', allow_blank=True)
    quantity = IntegerField('Qté', validators=[Optional(), NumberRange(min=1)])

class OrderForm(FlaskForm):
    order_type = SelectField('Type', choices=[('customer_order', 'Demande Client'), ('counter_production_request', 'Prod. Comptoir')], default='customer_order')
    customer_name = StringField('Nom du client', validators=[Optional(), Length(max=200)])
    customer_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    customer_address = TextAreaField('Adresse', validators=[Optional()])
    due_date = DateTimeField("Date de livraison/retrait", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    delivery_option = SelectField('Livraison', choices=[('pickup', 'Retrait'), ('delivery', 'Livraison')], default='pickup')
    delivery_cost = FloatField('Coût de livraison (€)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    items = FieldList(FormField(OrderItemForm), min_entries=1)
    submit = SubmitField('Enregistrer la commande')

class OrderStatusForm(FlaskForm):
    status = SelectField('Nouveau Statut', choices=[
        ('pending', 'En attente'),
        ('ready_at_shop', 'Prête en boutique'),
        ('out_for_delivery', 'En livraison'),
        ('completed', 'Terminée'),
        ('awaiting_payment', 'En attente de paiement'),
        ('cancelled', 'Annulée')
    ], validators=[DataRequired()])
    notes = TextAreaField('Ajouter une note (optionnel)', validators=[Optional()])
    submit = SubmitField('Mettre à jour le statut')
    
class RecipeIngredientForm(FlaskForm):
    product = QuerySelectField('Ingrédient', query_factory=ingredient_product_query_factory, get_label='name', allow_blank=True)
    quantity_needed = FloatField('Quantité', validators=[Optional(), NumberRange(min=0.001)])
    unit = StringField('Unité', validators=[Optional()])
    notes = StringField('Notes', validators=[Optional()])

class RecipeForm(FlaskForm):
    name = StringField('Nom de la recette', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Instructions', validators=[DataRequired()])
    finished_product = QuerySelectField('Produit Fini Associé', query_factory=finished_product_query_factory, get_label='name', allow_blank=False)
    yield_quantity = FloatField('Quantité Produite', validators=[DataRequired(), NumberRange(min=0.001)])
    yield_unit = StringField('Unité Produite', validators=[DataRequired()])
    preparation_time = IntegerField('Temps de préparation (min)', validators=[Optional(), NumberRange(min=0)])
    cooking_time = IntegerField('Temps de cuisson (min)', validators=[Optional(), NumberRange(min=0)])
    difficulty_level = SelectField('Difficulté', choices=[
        ('', 'Non spécifié'), ('Facile', 'Facile'), ('Moyen', 'Moyen'), ('Difficile', 'Difficile'), ('Expert', 'Expert')
    ], validators=[Optional()])
    ingredients = FieldList(FormField(RecipeIngredientForm), min_entries=1)
    submit = SubmitField('Enregistrer la Recette')