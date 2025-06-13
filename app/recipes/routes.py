# Fichier: app/recipes/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required
from extensions import db
from models import Recipe, Product, RecipeIngredient
from .forms import RecipeForm, ingredient_product_query_factory
from decorators import admin_required

recipes = Blueprint('recipes', __name__)

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
    
    # ### AJOUT : Préparation des données pour le JSON ###
    # On récupère tous les ingrédients possibles pour les passer au template.
    # On les transforme en une liste de dictionnaires pour être sérialisables en JSON.
    # C'est la correction clé pour le JavaScript du formulaire.
    all_ingredients = ingredient_product_query_factory().all()
    ingredients_json = [
        {'id': p.id, 'name': p.name, 'unit': p.unit} 
        for p in all_ingredients
    ]

    if form.validate_on_submit():
        try:
            recipe = Recipe()
            # On ne populate que les champs simples, pas le FieldList directement
            form.populate_obj(recipe)
            recipe.finished_product = form.finished_product.data
            
            db.session.add(recipe)
            db.session.flush() # flush pour obtenir l'ID de la recette

            # Traitement explicite des ingrédients
            recipe.ingredients = [] # Assure que la liste est vide avant ajout
            for item_data in form.ingredients.data:
                # On s'assure que l'ingrédient et la quantité sont bien présents
                if item_data.get('product') and item_data.get('quantity_needed') is not None:
                    # 'product' est déjà un objet Product grâce à WTForms, on peut l'utiliser directement
                    ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=item_data['product'].id,
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
            flash(f"Erreur inattendue lors de la création de la recette. Consulter les logs.", 'danger')
    
    if request.method == 'GET' and not form.ingredients.entries:
        form.ingredients.append_entry()
        
    return render_template(
        'recipes/recipe_form.html', 
        form=form, 
        title='Nouvelle Recette',
        # ### AJOUT : Passage des données JSON au template ###
        ingredient_products_json=ingredients_json
    )

@recipes.route('/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    form = RecipeForm(obj=recipe)
    
    # ### AJOUT : Préparation des données pour le JSON (identique à new_recipe) ###
    all_ingredients = ingredient_product_query_factory().all()
    # On ajoute le produit fini de la recette actuelle à la liste des choix, au cas où on voudrait le modifier
    if recipe.finished_product:
        form.finished_product.query = Product.query.filter_by(product_type='finished').filter((Product.recipe_definition == None) | (Product.id == recipe.product_id)).order_by(Product.name)

    ingredients_json = [
        {'id': p.id, 'name': p.name, 'unit': p.unit}
        for p in all_ingredients
    ]

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
            flash(f"Erreur inattendue lors de la mise à jour. Consulter les logs.", 'danger')

    if request.method == 'GET':
        # Re-populer le formulaire avec les données existantes
        form.process(obj=recipe)
        # Vider et re-remplir les ingrédients manuellement pour être sûr
        while len(form.ingredients.entries) > 0:
            form.ingredients.pop_entry()
        for item in recipe.ingredients:
            form.ingredients.append_entry(item)
    
    return render_template(
        'recipes/recipe_form.html', 
        form=form, 
        title=f"Modifier Recette: {recipe.name}", 
        edit_mode=True,
        # ### AJOUT : Passage des données JSON au template ###
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
        flash(f"Erreur lors de la suppression de la recette. Elle est peut-être utilisée ailleurs.", 'danger')
    return redirect(url_for('recipes.list_recipes'))