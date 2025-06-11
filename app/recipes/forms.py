from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, FloatField, 
                     IntegerField, FieldList, FormField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product

# Fonctions Factory pour les QuerySelectField
def ingredient_product_query_factory():
    return Product.query.filter_by(product_type='ingredient').order_by(Product.name)

def finished_product_query_factory():
    # On ne montre que les produits finis qui n'ont pas encore de recette
    # Le 'not_' est importé de sqlalchemy, mais cette syntaxe fonctionne aussi
    return Product.query.filter_by(product_type='finished').filter(Product.recipe_definition == None).order_by(Product.name)


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
        ('', 'Non spécifié'), 
        ('Facile', 'Facile'), 
        ('Moyen', 'Moyen'), 
        ('Difficile', 'Difficile'), 
        ('Expert', 'Expert')
    ], validators=[Optional()])
    ingredients = FieldList(FormField(RecipeIngredientForm), min_entries=1, label="Ingrédients")
    submit = SubmitField('Enregistrer la Recette')