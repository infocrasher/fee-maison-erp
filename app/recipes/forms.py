# Fichier: app/recipes/forms.py

from flask_wtf import FlaskForm
# ### CORRECTION : Import de la classe 'Form' de base de WTForms ###
from wtforms import (
    Form,  # On importe la classe de base pour les sous-formulaires
    StringField, 
    TextAreaField, 
    FieldList, 
    FormField, 
    SubmitField, 
    SelectField, 
    DecimalField, 
    IntegerField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.widgets import HiddenInput
from models import Product, Recipe
from sqlalchemy import or_

# ==============================================================================
#  HELPER FUNCTION
# ==============================================================================

def ingredient_product_query_factory():
    """
    Retourne une requête pour obtenir tous les produits de type 'ingrédient'.
    """
    return Product.query.filter_by(product_type='ingredient').order_by(Product.name)


# ==============================================================================
#  SUB-FORM FOR A SINGLE INGREDIENT
# ==============================================================================

# ### CORRECTION : Le sous-formulaire doit hériter de 'Form', et non de 'FlaskForm' ###
class IngredientForm(Form):
    """
    Sous-formulaire représentant une seule ligne d'ingrédient dans la recette.
    Il ne gère pas le CSRF lui-même, il fait partie du formulaire principal.
    """
    id = IntegerField(widget=HiddenInput(), validators=[Optional()])
    product = SelectField('Ingrédient', coerce=int, validators=[DataRequired("Veuillez choisir un ingrédient.")])
    quantity_needed = DecimalField('Quantité', validators=[DataRequired("La quantité est requise."), NumberRange(min=0.001)])
    unit = StringField('Unité', validators=[DataRequired(), Length(max=50)])
    notes = StringField('Notes', validators=[Optional(), Length(max=200)])

    def __init__(self, *args, **kwargs):
        """
        Constructeur pour populer dynamiquement la liste des choix d'ingrédients.
        """
        super(IngredientForm, self).__init__(*args, **kwargs)
        self.product.choices = [(p.id, f"{p.name} ({p.unit})") for p in ingredient_product_query_factory().all()]
        self.product.choices.insert(0, (0, '-- Choisir un ingrédient --'))


# ==============================================================================
#  MAIN FORM FOR A RECIPE (Hérite bien de FlaskForm)
# ==============================================================================

class RecipeForm(FlaskForm):
    """
    Formulaire principal pour la création et l'édition d'une recette.
    C'est LUI qui gère la sécurité CSRF pour l'ensemble.
    """
    name = StringField('Nom de la recette', validators=[DataRequired("Le nom est requis."), Length(max=100)])
    description = TextAreaField('Description / Instructions', validators=[Optional(), Length(max=5000)])
    
    yield_quantity = IntegerField(
        'Quantité Produite', 
        validators=[DataRequired("La quantité produite est requise."), NumberRange(min=1, message="Le rendement doit être d'au moins 1.")], 
        default=1,
        description="Combien d'unités cette recette produit-elle ? (ex: 112)"
    )
    yield_unit = StringField(
        'Unité Produite', 
        validators=[DataRequired("L'unité produite est requise."), Length(max=50)], 
        default='pièces',
        description="Quelle est l'unité ? (ex: pièces, portions, gâteaux)"
    )

    finished_product = SelectField('Produit Fini Associé', coerce=int, validators=[Optional()])
    ingredients = FieldList(FormField(IngredientForm), min_entries=1, label="Ingrédients")
    submit = SubmitField('Enregistrer la Recette')

    def __init__(self, *args, **kwargs):
        """
        Constructeur pour populer dynamiquement la liste des produits finis.
        """
        super(RecipeForm, self).__init__(*args, **kwargs)
        
        recipe_obj = kwargs.get('obj')
        
        query = Product.query.filter_by(product_type='finished')
        
        if recipe_obj and recipe_obj.product_id:
            query = query.filter(or_(Product.recipe_definition == None, Product.id == recipe_obj.product_id))
        else:
            query = query.filter(Product.recipe_definition == None)
        
        self.finished_product.choices = [(p.id, p.name) for p in query.order_by(Product.name).all()]
        self.finished_product.choices.insert(0, (0, '-- Aucun --'))