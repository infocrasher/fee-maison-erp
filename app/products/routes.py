# Fichier: app/products/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required
from extensions import db
from models import Product, Category
from .forms import ProductForm, CategoryForm # Import local
from decorators import admin_required

products = Blueprint('products', __name__)

# --- ROUTES POUR LES CATÉGORIES ---
@products.route('/categories')
@login_required
@admin_required
def list_categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('products/list_categories.html', categories=categories, title='Catégories')

@products.route('/category/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        flash('Nouvelle catégorie ajoutée.', 'success')
        return redirect(url_for('products.list_categories'))
    return render_template('products/category_form.html', form=form, title='Nouvelle Catégorie')

@products.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    category = db.session.get(Category, category_id) or abort(404)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash('Catégorie mise à jour.', 'success')
        return redirect(url_for('products.list_categories'))
    return render_template('products/category_form.html', form=form, title=f'Modifier: {category.name}')

@products.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = db.session.get(Category, category_id) or abort(404)
    if category.products.first():
        flash('Impossible de supprimer une catégorie contenant des produits.', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Catégorie supprimée.', 'success')
    return redirect(url_for('products.list_categories'))


# --- ROUTES POUR LES PRODUITS ---
@products.route('/')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    pagination = Product.query.order_by(Product.name).paginate(page=page, per_page=current_app.config['PRODUCTS_PER_PAGE'])
    return render_template('products/list_products.html', products_pagination=pagination, title='Produits')

@products.route('/<int:product_id>')
@login_required
def view_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    return render_template('products/view_product.html', product=product, title=product.name)

@products.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product()
        form.populate_obj(product)
        product.category = form.category.data
        db.session.add(product)
        db.session.commit()
        flash(f'Le produit "{product.name}" a été créé.', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/product_form.html', form=form, title='Nouveau Produit')

@products.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        form.populate_obj(product)
        product.category = form.category.data
        db.session.commit()
        flash(f'Le produit "{product.name}" a été mis à jour.', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/product_form.html', form=form, title=f'Modifier: {product.name}')

@products.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    if product.recipe_uses.first() or product.order_items.first() or product.recipe_definition:
        flash(f"Produit '{product.name}' est utilisé et ne peut être supprimé.", 'danger')
    else:
        db.session.delete(product)
        db.session.commit()
        flash('Produit supprimé.', 'success')
    return redirect(url_for('products.list_products'))