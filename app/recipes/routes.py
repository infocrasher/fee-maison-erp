# Fichier: app/recipes/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required
from extensions import db
from models import Recipe, Product, RecipeIngredient
from .forms import RecipeForm, ingredient_product_query_factory
from decorators import admin_required

recipes = Blueprint('recipes', __name__, url_prefix='/admin/recipes') # J'ajoute un préfixe pour la clarté

@recipes.route('/')
@login_required
@admin_required
def list_recipes():
    page = request.args.get('page', 1, type=int)
    pagination = Recipe.query.order_by(Recipe.name).paginate(page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 10))
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
    
    # ### MODIFICATION : On ajoute le cost_price au JSON ###
    all_ingredients = ingredient_product_query_factory().all()
    ingredients_json = [
        {
            'id': p.id, 
            'name': p.name, 
            'unit': p.unit, 
            # On convertit le Decimal en float pour le JSON
            'cost_price': float(p.cost_price) if p.cost_price is not None else 0.0 
        } 
        for p in all_ingredients
    ]

    if form.validate_on_submit():
        try:
            recipe = Recipe()
            form.populate_obj(recipe)
            recipe.finished_product = form.finished_product.data
            
            db.session.add(recipe)
            db.session.flush()

            recipe.ingredients = []
            for item_data in form.ingredients.data:
                if item_data.get('product') and item_data.get('quantity_needed') is not None:
                    ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=item_data['product'].id,
                        quantity_needed=item_data['quantity_needed'],
                        unit=item_data['unit'], # L'unité est celle saisie (ex: G ou ML)
                        notes=item_data['notes']
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash(f"Recette '{recipe.name}' créée avec succès.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la création de la recette: {e}", exc_info=True)
            flash(f"Erreur inattendue lors de la création. Consulter les logs.", 'danger')
    
    # Gérer les erreurs de validation pour le débogage
    if form.errors:
        flash("Le formulaire contient des erreurs. Veuillez les corriger.", "danger")
        current_app.logger.warning(f"Erreurs de validation du formulaire de recette : {form.errors}")

    if request.method == 'GET' and not form.ingredients.entries:
        form.ingredients.append_entry()
        
    return render_template(
        'recipes/recipe_form.html', 
        form=form, 
        title='Nouvelle Recette',
        ingredient_products_json=ingredients_json
    )


# La route edit_recipe doit aussi être mise à jour de la même manière pour le JSON
@recipes.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    form = RecipeForm(obj=recipe)
    
    # ### MODIFICATION : On ajoute le cost_price au JSON (identique à new_recipe) ###
    all_ingredients = ingredient_product_query_factory().all()
    ingredients_json = [
        {
            'id': p.id, 
            'name': p.name, 
            'unit': p.unit, 
            'cost_price': float(p.cost_price) if p.cost_price is not None else 0.0
        }
        for p in all_ingredients
    ]
    
    # Logique pour le champ select du produit fini
    if recipe.finished_product:
        form.finished_product.query = Product.query.filter_by(product_type='finished').filter((Product.recipe_definition == None) | (Product.id == recipe.product_id)).order_by(Product.name)

    if form.validate_on_submit():
        try:
            # Vider et reconstruire proprement
            RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
            db.session.flush()

            form.populate_obj(recipe)
            recipe.finished_product = form.finished_product.data
            
            for item_data in form.ingredients.data:
                 if item_data.get('product') and item_data.get('quantity_needed') is not None:
                    ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=item_data['product'].id,
                        quantity_needed=item_data['quantity_needed'],
                        unit=item_data['unit'],
                        notes=item_data['notes']
                    )
                    db.session.add(ingredient)
            
            db.session.commit()
            flash(f"Recette '{recipe.name}' mise à jour.", 'success')
            return redirect(url_for('recipes.view_recipe', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la mise à jour: {e}", exc_info=True)
            flash(f"Erreur inattendue lors de la mise à jour.", 'danger')

    if form.errors:
        flash("Le formulaire contient des erreurs. Veuillez les corriger.", "danger")
        current_app.logger.warning(f"Erreurs de validation du formulaire de recette (edit) : {form.errors}")
    
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
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    try:
        db.session.delete(recipe)
        db.session.commit()
        flash(f"Recette '{recipe.name}' supprimée.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de la recette {recipe_id}: {e}", exc_info=True)
        flash(f"Erreur lors de la suppression de la recette.", 'danger')
    return redirect(url_for('recipes.list_recipes'))