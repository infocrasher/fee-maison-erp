# Fichier: app/recipes/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required
from extensions import db
from models import Recipe, Product, RecipeIngredient
from .forms import RecipeForm, ingredient_product_query_factory
from decorators import admin_required

# On définit le Blueprint pour le module des recettes
recipes = Blueprint('recipes', __name__, url_prefix='/admin/recipes')

@recipes.route('/')
@login_required
@admin_required
def list_recipes():
    """Affiche la liste paginée de toutes les recettes."""
    page = request.args.get('page', 1, type=int)
    pagination = Recipe.query.order_by(Recipe.name).paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 10)
    )
    return render_template('recipes/list_recipes.html', recipes_pagination=pagination, title='Gestion des Recettes')

@recipes.route('/<int:recipe_id>')
@login_required
@admin_required
def view_recipe(recipe_id):
    """Affiche les détails d'une recette spécifique."""
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    return render_template('recipes/view_recipe.html', recipe=recipe, title=f"Recette : {recipe.name}")

@recipes.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_recipe():
    """Gère la création d'une nouvelle recette."""
    form = RecipeForm()
    
    # Préparation des données JSON pour le JavaScript du template (calcul des coûts)
    all_ingredients = ingredient_product_query_factory().all()
    ingredients_json = [
        {'id': p.id, 'name': p.name, 'unit': p.unit, 'cost_price': float(p.cost_price) if p.cost_price is not None else 0.0} 
        for p in all_ingredients
    ]

    if form.validate_on_submit():
        try:
            # Création manuelle de l'objet pour une meilleure maîtrise
            recipe = Recipe(
                name=form.name.data,
                description=form.description.data,
                yield_quantity=form.yield_quantity.data,
                yield_unit=form.yield_unit.data,
                product_id=form.product_id.data if form.product_id.data > 0 else None
            )
            db.session.add(recipe)
            db.session.flush()  # Obtenir l'ID de la recette pour les ingrédients

            # Ajout des ingrédients
            for item_data in form.ingredients.data:
                if item_data.get('product') and item_data.get('quantity_needed') is not None:
                    ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=item_data['product'],
                        quantity_needed=item_data['quantity_needed'],
                        unit=item_data['unit'],
                        notes=item_data['notes']
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash(f"Recette '{recipe.name}' créée avec succès.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la création de la recette: {e}", exc_info=True)
            flash("Erreur inattendue lors de la création. Consulter les logs.", 'danger')
    
    if form.errors:
        flash("Le formulaire contient des erreurs. Veuillez les corriger.", "danger")
        current_app.logger.warning(f"Erreurs de validation du formulaire de recette (new): {form.errors}")

    return render_template('recipes/recipe_form.html', form=form, title='Nouvelle Recette', ingredient_products_json=ingredients_json)

@recipes.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_recipe(recipe_id):
    """Gère l'édition d'une recette existante."""
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    # On pré-remplit le formulaire avec les données de l'objet recette
    form = RecipeForm(obj=recipe)

    # Préparation des données JSON pour le JavaScript
    all_ingredients = ingredient_product_query_factory().all()
    ingredients_json = [
        {'id': p.id, 'name': p.name, 'unit': p.unit, 'cost_price': float(p.cost_price) if p.cost_price is not None else 0.0}
        for p in all_ingredients
    ]

    if form.validate_on_submit():
        try:
            # Mise à jour des champs de la recette principale
            recipe.name = form.name.data
            recipe.description = form.description.data
            recipe.yield_quantity = form.yield_quantity.data
            recipe.yield_unit = form.yield_unit.data
            recipe.product_id = form.product_id.data if form.product_id.data > 0 else None

            # Stratégie de mise à jour des ingrédients : supprimer les anciens, recréer les nouveaux
            RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
            db.session.flush()

            for item_data in form.ingredients.data:
                if item_data.get('product') and item_data.get('quantity_needed') is not None:
                    ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=item_data['product'],
                        quantity_needed=item_data['quantity_needed'],
                        unit=item_data['unit'],
                        notes=item_data['notes']
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash(f"Recette '{recipe.name}' mise à jour avec succès.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la mise à jour de la recette {recipe_id}: {e}", exc_info=True)
            flash("Erreur inattendue lors de la mise à jour. Consulter les logs.", 'danger')

    if form.errors:
        flash("Le formulaire contient des erreurs. Veuillez les corriger.", "danger")
        current_app.logger.warning(f"Erreurs de validation du formulaire de recette (edit {recipe_id}): {form.errors}")
    
    # Repopulation manuelle des ingrédients pour le rendu GET initial
    # C'est nécessaire car WTForms ne gère pas bien la repopulation de FieldList avec des données complexes
    while len(form.ingredients.entries) > 0:
        form.ingredients.pop_entry()
    for item in recipe.ingredients:
        form.ingredients.append_entry({
            'product': item.product_id,
            'quantity_needed': item.quantity_needed,
            'unit': item.unit,
            'notes': item.notes
        })

    return render_template(
        'recipes/recipe_form.html', 
        form=form, 
        title=f"Modifier Recette: {recipe.name}", 
        edit_mode=True,
        ingredient_products_json=ingredients_json
    )

@recipes.route('/<int:recipe_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_recipe(recipe_id):
    """Gère la suppression d'une recette."""
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    recipe_name = recipe.name
    try:
        db.session.delete(recipe)
        db.session.commit()
        flash(f"La recette '{recipe_name}' a été supprimée.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de la recette {recipe_id}: {e}", exc_info=True)
        flash("Erreur lors de la suppression de la recette. Elle est peut-être liée à d'autres éléments.", 'danger')
    return redirect(url_for('recipes.list_recipes'))