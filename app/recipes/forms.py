# Fichier: app/recipes/forms.py

from flask_wtf import FlaskForm
from wtforms import (
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
    Utiliser une factory permet de ne pas exécuter la requête au chargement du module.
    """
    return Product.query.filter_by(product_type='ingredient').order_by(Product.name)


# ==============================================================================
#  SUB-FORM FOR A SINGLE INGREDIENT
# ==============================================================================

class IngredientForm(FlaskForm):
    """
    Sous-formulaire représentant une seule ligne d'ingrédient dans la recette.
    """
    # Champ caché pour stocker l'ID de l'ingrédient en mode édition
    id = IntegerField(widget=HiddenInput(), validators=[Optional()])
    
    # Champ de sélection pour choisir l'ingrédient
    product = SelectField('Ingrédient', coerce=int, validators=[DataRequired("Veuillez choisir un ingrédient.")])
    
    # Champ pour la quantité nécessaire (ex: 500.5)
    quantity_needed = DecimalField('Quantité', validators=[DataRequired("La quantité est requise."), NumberRange(min=0.001)])
    
    # Champ pour l'unité de la quantité (ex: 'G', 'ML', 'pièces')
    unit = StringField('Unité', validators=[DataRequired(), Length(max=50)])
    
    # Champ optionnel pour des notes sur l'ingrédient
    notes = StringField('Notes', validators=[Optional(), Length(max=200)])

    def __init__(self, *args, **kwargs):
        """
        Constructeur pour populer dynamiquement la liste des choix d'ingrédients.
        """
        super(IngredientForm, self).__init__(*args, **kwargs)
        # On ne peuple les choix que si ce n'est pas une requête POST (pour préserver les données soumises)
        if not self.is_submitted():
             self.product.choices = [(p.id, f"{p.name} ({p.unit})") for p in ingredient_product_query_factory().all()]
             self.product.choices.insert(0, (0, '-- Choisir un ingrédient --'))


# ==============================================================================
#  MAIN FORM FOR A RECIPE
# ==============================================================================

class RecipeForm(FlaskForm):
    """
    Formulaire principal pour la création et l'édition d'une recette.
    """
    name = StringField('Nom de la recette', validators=[DataRequired("Le nom est requis."), Length(max=100)])
    description = TextAreaField('Description / Instructions', validators=[Optional(), Length(max=5000)])
    
    # --- Champs pour la logique de rendement (Yield) ---
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
    # --- Fin des champs de rendement ---

    finished_product = SelectField('Produit Fini Associé', coerce=int, validators=[Optional()])
    
    # Liste dynamique des sous-formulaires d'ingrédients
    ingredients = FieldList(FormField(IngredientForm), min_entries=1, label="Ingrédients")
    
    submit = SubmitField('Enregistrer la Recette')

    def __init__(self, *args, **kwargs):
        """
        Constructeur pour populer dynamiquement la liste des produits finis.
        """
        super(RecipeForm, self).__init__(*args, **kwargs)
        
        # On ne peuple les choix que si ce n'est pas une requête POST
        if not self.is_submitted():
            # Logique pour le mode édition : on veut pouvoir re-sélectionner le produit déjà associé
            recipe_obj = kwargs.get('obj')
            
            query = Product.query.filter_by(product_type='finished')
            
            # Si on est en mode édition, on inclut les produits sans recette ET le produit actuellement lié
            if recipe_obj and recipe_obj.product_id:
                query = query.filter(or_(Product.recipe_definition == None, Product.id == recipe_obj.product_id))
            else: # Sinon, on ne montre que les produits sans recette
                query = query.filter(Product.recipe_definition == None)
            
            self.finished_product.choices = [(p.id, p.name) for p in query.order_by(Product.name).all()]
            self.finished_product.choices.insert(0, (0, '-- Aucun --'))