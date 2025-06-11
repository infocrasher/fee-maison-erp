# Fichier: app/recipes/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required
from extensions import db
from models import Recipe, Product, RecipeIngredient
from .forms import RecipeForm
from decorators import admin_required

recipes = Blueprint('recipes', __name__)

@recipes.route('/')
@login_required
@admin_required
def list_recipes():
    page = request.args.get('page', 1, type=int)
    pagination = Recipe.query.order_by(Recipe.name).paginate(page=page, per_page=current_app.config['PRODUCTS_PER_PAGE'])
    return render_template('recipes/list_recipes.html', recipes_pagination=pagination, title='Gestion des Recettes')

@recipes.route('/<int:recipe_id>')
@login_required
@admin_required
def view_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    return render_template('recipes/view_recipe.html', recipe=recipe, title=f"Recette: {recipe.name}")

@recipes.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        try:
            recipe = Recipe()
            form.populate_obj(recipe)
            recipe.finished_product = form.finished_product.data
            db.session.add(recipe)
            db.session.flush()
            for item_data in form.ingredients.data:
                if item_data.get('product') and item_data.get('quantity_needed'):
                    ingredient = RecipeIngredient(recipe_id=recipe.id, **item_data)
                    db.session.add(ingredient)
            db.session.commit()
            flash(f"Recette '{recipe.name}' créée avec succès.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création de la recette: {e}", 'danger')
    
    # Pré-remplir avec une ligne d'ingrédient vide pour le template
    if request.method == 'GET' and not form.ingredients.entries:
        form.ingredients.append_entry()
        
    return render_template('recipes/recipe_form.html', form=form, title='Nouvelle Recette')

@recipes.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        try:
            # Vider les anciens ingrédients
            for item in recipe.ingredients:
                db.session.delete(item)
            db.session.flush()

            form.populate_obj(recipe)
            recipe.finished_product = form.finished_product.data
            
            # Ajouter les nouveaux
            for item_data in form.ingredients.data:
                 if item_data.get('product') and item_data.get('quantity_needed'):
                    ingredient = RecipeIngredient(recipe_id=recipe.id, **item_data)
                    db.session.add(ingredient)
            
            db.session.commit()
            flash(f"Recette '{recipe.name}' mise à jour.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour: {e}", 'danger')

    if request.method == 'GET':
        form.ingredients.entries = []
        for item in recipe.ingredients:
            form.ingredients.append_entry(item)
    
    return render_template('recipes/recipe_form.html', form=form, title=f"Modifier Recette: {recipe.name}", edit_mode=True)

@recipes.route('/<int:recipe_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    db.session.delete(recipe)
    db.session.commit()
    flash(f"Recette '{recipe.name}' supprimée.", 'success')
    return redirect(url_for('recipes.list_recipes'))