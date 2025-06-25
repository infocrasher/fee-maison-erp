# Fichier: app/products/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Category

def category_query_factory():
    return Category.query.order_by(Category.name)

class CategoryForm(FlaskForm):
    name = StringField('Nom de la catégorie', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Enregistrer')

class ProductForm(FlaskForm):
    name = StringField('Nom du produit', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    sku = StringField('SKU / Référence', validators=[Optional(), Length(max=50)])
    product_type = SelectField(
    'Type', 
    choices=[
        ('ingredient', 'Ingrédient'),
        ('finished', 'Produit Fini'),
        ('consommable', 'Consommable') # On ajoute l'option ici
    ], 
    validators=[DataRequired()]
)
    unit = StringField('Unité (ex: kg, L, pièce)', validators=[DataRequired(), Length(max=20)])
    price = FloatField('Prix de vente (DA)', validators=[Optional(), NumberRange(min=0)])
    cost_price = FloatField("Prix d'achat / Coût de revient (DA)", validators=[Optional(), NumberRange(min=0)])
    quantity_in_stock = FloatField('Quantité en stock', default=0, validators=[DataRequired(), NumberRange(min=0)])
    category = QuerySelectField('Catégorie', query_factory=category_query_factory, get_label='name', allow_blank=False)
    submit = SubmitField('Enregistrer le produit')