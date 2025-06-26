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
        'Type de Produit', 
        choices=[
            ('ingredient', 'Ingrédient'), 
            ('finished', 'Produit Fini'),
            ('consommable', 'Consommable')
        ], 
        validators=[DataRequired()]
    )
    
    # ### DEBUT DE LA CORRECTION ###
    # Le champ "Unité" devient un SelectField pour choisir l'unité de BASE
    unit = SelectField(
        'Unité de Base (pour Stock et Recettes)', 
        choices=[
            ('g', 'Grammes (g)'),
            ('ml', 'Millilitres (ml)'),
            ('pièce', 'Pièce / Unité')
        ], 
        validators=[DataRequired()]
    )
    # ### FIN DE LA CORRECTION ###

    price = FloatField('Prix de vente (DA)', validators=[Optional(), NumberRange(min=0)])
    
    # On clarifie le label pour le coût
    cost_price = FloatField("Coût de Revient Initial / PMP (DA par unité de base)", 
                            validators=[Optional(), NumberRange(min=0)],
                            description="Sera mis à jour automatiquement par les achats (PMP).")
    
    # On retire le champ 'quantity_in_stock' qui était source de confusion.
    # Le stock initial sera géré par un "Ajustement de stock" ou un premier achat.
    
    category = QuerySelectField('Catégorie', query_factory=category_query_factory, get_label='name', allow_blank=False)
    submit = SubmitField('Enregistrer le produit')