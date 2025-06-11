import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, url_for, flash, redirect, request, abort, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import func
from markupsafe import Markup, escape

from extensions import db, migrate, login
from config import config_by_name
from forms import (LoginForm, ChangePasswordForm, CategoryForm, ProductForm, StockAdjustmentForm,
                   QuickStockEntryForm, OrderForm, OrderStatusForm, RecipeForm)
from models import (User, Category, Product, Order, OrderItem, Recipe,
                    RecipeIngredient, CONVERSION_FACTORS)
from decorators import admin_required


def get_unit_suggestion(ingredient_name: str, base_unit: str = None) -> str:
    name_lower = ingredient_name.lower()
    if base_unit and base_unit.lower() in ['g', 'ml', 'pièce', 'unité', 'grammes', 'millilitre']:
        return base_unit
    if any(word in name_lower for word in ['huile', 'lait', 'eau', 'vinaigre', 'sirop', 'crème', 'liquide']):
        return 'ml'
    elif any(word in name_lower for word in ['farine', 'sucre', 'sel', 'levure', 'cacao', 'poudre', 'semoule', 'maïzena', 'fécule', 'beurre', 'fromage', 'viande', 'poisson', 'pate']):
        return 'g'
    elif any(word in name_lower for word in ['oeuf', 'citron', 'orange', 'pomme', 'banane', 'oignon', 'gousse', 'tomate', 'feuille']):
        return 'pièce'
    return base_unit if base_unit and base_unit.strip() else 'g'


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    login.login_view = 'login'
    login.login_message_category = 'info'
    login.login_message = "Veuillez vous connecter pour accéder à cette page."

    @login.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/fee_maison.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Fée Maison startup')

    @app.context_processor
    def inject_manual_csrf_token():
        return dict(manual_csrf_token=generate_csrf)

    @app.template_filter('nl2br')
    def nl2br_filter(s):
        return Markup(escape(s).replace('\n', '<br>\n')) if s else ''

    # --- ROUTES GÉNÉRALES ---
    @app.route('/')
    @app.route('/home')
    def hello_world():
        return render_template('home.html', title='Accueil')

    @app.route("/login", methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Email ou mot de passe incorrect.', 'danger')
        return render_template('login.html', form=form, title='Connexion')

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash('Vous avez été déconnecté.', 'info')
        return redirect(url_for('hello_world'))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        now_utc = datetime.now(timezone.utc)
        start_of_month_utc = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        sales_data = db.session.query(func.count(Order.id), func.sum(Order.total_amount)).filter(
            Order.order_type == 'customer_order', Order.status == 'completed', Order.created_at >= start_of_month_utc
        ).one()
        sales_count_month = sales_data[0] or 0
        total_revenue_month = sales_data[1] or Decimal('0.00')
        active_products_count = Product.query.filter(Product.quantity_in_stock > 0).count()
        total_items_in_stock = db.session.query(func.sum(Product.quantity_in_stock)).scalar() or 0
        dashboard_data = {'sales_count_month': sales_count_month, 'total_revenue_month': total_revenue_month,
                          'active_products_count': active_products_count, 'total_items_in_stock': total_items_in_stock}
        return render_template('dashboard.html', title='Tableau de Bord', data=dashboard_data)

    @app.route('/account', methods=['GET', 'POST'])
    @login_required
    def account():
        form = ChangePasswordForm()
        if form.validate_on_submit():
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Votre mot de passe a été mis à jour.', 'success')
            return redirect(url_for('account'))
        return render_template('account.html', form=form, title='Mon Compte')

    # --- ROUTES D'ADMINISTRATION ---
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        return render_template('admin/admin_dashboard.html', title='Administration')

    # == GESTION DES CATÉGORIES ==
    @app.route('/admin/categories')
    @login_required
    @admin_required
    def list_categories():
        categories = Category.query.order_by(Category.name).all()
        return render_template('admin/categories/list_categories.html', categories=categories, title='Catégories')

    @app.route('/admin/category/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def new_category():
        form = CategoryForm()
        if form.validate_on_submit():
            category = Category(name=form.name.data, description=form.description.data)
            db.session.add(category)
            db.session.commit()
            flash('Nouvelle catégorie ajoutée.', 'success')
            return redirect(url_for('list_categories'))
        return render_template('admin/categories/category_form.html', form=form, title='Nouvelle Catégorie')

    @app.route('/admin/category/<int:category_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_category(category_id):
        category = db.session.get(Category, category_id) or abort(404)
        form = CategoryForm(obj=category)
        if form.validate_on_submit():
            form.populate_obj(category)
            db.session.commit()
            flash('Catégorie mise à jour.', 'success')
            return redirect(url_for('list_categories'))
        return render_template('admin/categories/category_form.html', form=form, title=f'Modifier: {category.name}')

    @app.route('/admin/category/<int:category_id>/delete', methods=['POST'])
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
        return redirect(url_for('list_categories'))

    # == GESTION DES PRODUITS ==
    @app.route('/products')
    @login_required
    def list_products():
        page = request.args.get('page', 1, type=int)
        pagination = Product.query.order_by(Product.name).paginate(page=page, per_page=app.config['PRODUCTS_PER_PAGE'])
        return render_template('products/list_products.html', products_pagination=pagination, title='Produits')

    @app.route('/product/<int:product_id>')
    @login_required
    def view_product(product_id):
        product = db.session.get(Product, product_id) or abort(404)
        return render_template('products/view_product.html', product=product, title=product.name)

    @app.route('/admin/product/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def new_product():
        form = ProductForm(request.form)
        if form.validate_on_submit():
            product = Product()
            form.populate_obj(product)
            product.category_id = form.category.data.id
            db.session.add(product)
            db.session.commit()
            flash(f'Le produit "{product.name}" a été créé.', 'success')
            return redirect(url_for('list_products'))
        return render_template('products/product_form.html', form=form, title='Nouveau Produit')

    @app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_product(product_id):
        product = db.session.get(Product, product_id) or abort(404)
        form = ProductForm(request.form, obj=product) if request.method == 'POST' else ProductForm(obj=product)
        if form.validate_on_submit():
            form.populate_obj(product)
            product.category_id = form.category.data.id
            db.session.commit()
            flash(f'Le produit "{product.name}" a été mis à jour.', 'success')
            return redirect(url_for('list_products'))
        return render_template('products/product_form.html', form=form, title=f'Modifier: {product.name}')

    @app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
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
        return redirect(url_for('list_products'))
    
    # == GESTION DU STOCK ==
    @app.route('/admin/stock_adjustment', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def stock_adjustment():
        form = StockAdjustmentForm()
        if form.validate_on_submit():
            product_obj = form.product.data
            quantity_change = form.quantity.data
            reason = form.reason.data.strip() if form.reason.data else "Ajustement manuel"
            old_stock = product_obj.quantity_in_stock
            new_stock = (old_stock or 0) + quantity_change
            if new_stock < 0:
                flash(f'Le stock de "{product_obj.name}" ne peut pas devenir négatif.', 'danger')
            else:
                product_obj.quantity_in_stock = new_stock
                db.session.commit()
                flash(f'Stock de "{product_obj.name}" ajusté à {new_stock}.', 'success')
                return redirect(url_for('stock_adjustment'))
        return render_template('admin/stock_adjustment_form.html', form=form, title='Ajustement de Stock')

    @app.route('/admin/quick_stock_entry', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def quick_stock_entry():
        form = QuickStockEntryForm()
        if form.validate_on_submit():
            product_obj = form.product.data
            quantity_received = form.quantity_received.data
            product_obj.quantity_in_stock = (product_obj.quantity_in_stock or 0) + quantity_received
            db.session.commit()
            flash(f'Stock pour "{product_obj.name}" mis à jour : {product_obj.quantity_in_stock}.', 'success')
            return redirect(url_for('quick_stock_entry'))
        return render_template('admin/quick_stock_entry.html', form=form, title='Réception Rapide')

    @app.route('/admin/stock_overview')
    @login_required
    @admin_required
    def stock_overview():
        low_stock_threshold = app.config.get('LOW_STOCK_THRESHOLD', 5)
        # S'assure que le filtre fonctionne même si la quantité est None
        low_stock_products = Product.query.filter(Product.quantity_in_stock != None, Product.quantity_in_stock > 0, Product.quantity_in_stock < low_stock_threshold).order_by(Product.quantity_in_stock).all()
        out_of_stock_products = Product.query.filter((Product.quantity_in_stock == 0) | (Product.quantity_in_stock == None)).order_by(Product.name).all()
        return render_template('admin/stock_overview.html', title="Vue d'ensemble du Stock", low_stock_products=low_stock_products, out_of_stock_products=out_of_stock_products)

    # == GESTION DES COMMANDES ==
    @app.route('/admin/orders')
    @login_required
    @admin_required
    def list_orders():
        page = request.args.get('page', 1, type=int)
        orders_pagination = Order.query.order_by(Order.due_date.desc()).paginate(page=page, per_page=app.config.get('ORDERS_PER_PAGE', 10))
        return render_template('admin/orders/list_orders.html', orders_pagination=orders_pagination, title='Gestion des Commandes')

    @app.route('/admin/order/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def new_order():
        form = OrderForm()
        if form.validate_on_submit():
            order = Order(user_id=current_user.id)
            form.populate_obj(order)
            db.session.add(order)
            db.session.flush()
            
            for item_data in form.items.data:
                if item_data['product'] and item_data['quantity'] > 0:
                    product = item_data['product']
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item_data['quantity'],
                        unit_price=product.price or Decimal('0.00')
                    )
                    db.session.add(order_item)
            
            order.calculate_total_amount()
            db.session.commit()
            flash('Nouvelle commande créée.', 'success')
            return redirect(url_for('view_order', order_id=order.id))
        return render_template('admin/orders/order_form_multifield.html', form=form, title='Nouvelle Commande')

    @app.route('/admin/order/<int:order_id>')
    @login_required
    @admin_required
    def view_order(order_id):
        order = db.session.get(Order, order_id) or abort(404)
        return render_template('admin/orders/view_order.html', order=order, title=f'Commande #{order.id}')

    @app.route('/admin/order/<int:order_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_order(order_id):
        order = db.session.get(Order, order_id) or abort(404)
        form = OrderForm(request.form, obj=order) if request.method == 'POST' else OrderForm(obj=order)
        if request.method == 'GET':
            form.items.entries = [] # Vider la liste
            for item in order.items:
                form.items.append_entry(item)

        if form.validate_on_submit():
            form.populate_obj(order)
            
            # Suppression des anciens items
            for item in order.items:
                db.session.delete(item)
            db.session.flush()
            
            # Ajout des nouveaux
            for item_data in form.items.data:
                if item_data['product'] and item_data['quantity'] > 0:
                    product = item_data['product']
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item_data['quantity'],
                        unit_price=product.price or Decimal('0.00')
                    )
                    db.session.add(order_item)
            
            order.calculate_total_amount()
            db.session.commit()
            flash('Commande mise à jour.', 'success')
            return redirect(url_for('view_order', order_id=order.id))
        return render_template('admin/orders/order_form_multifield.html', form=form, title=f'Modifier Commande #{order.id}', edit_mode=True)

    @app.route('/admin/order/<int:order_id>/edit_status', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_order_status(order_id):
        order = db.session.get(Order, order_id) or abort(404)
        form = OrderStatusForm(obj=order)
        if form.validate_on_submit():
            order.status = form.status.data
            if form.notes.data:
                order.notes = (order.notes or '') + f"\n---\nNote du {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}: {form.notes.data}"
            db.session.commit()
            flash('Statut de la commande mis à jour.', 'success')
            return redirect(url_for('view_order', order_id=order.id))
        return render_template('admin/orders/order_status_form.html', form=form, order=order, title='Modifier Statut')

    @app.route('/admin/orders/calendar')
    @login_required
    @admin_required
    def orders_calendar():
        orders = Order.query.filter(Order.due_date.isnot(None)).all()
        events = []
        for order in orders:
            events.append({
                'id': order.id,
                'title': f"#{order.id} - {order.customer_name}",
                'start': order.due_date.isoformat(),
                'url': url_for('view_order', order_id=order.id)
            })
        return render_template('admin/orders/orders_calendar.html', events=events, title="Calendrier des Commandes")

    # == GESTION DES RECETTES ==
    @app.route('/admin/recipes')
    @login_required
    @admin_required
    def list_recipes():
        page = request.args.get('page', 1, type=int)
        recipes_pagination = Recipe.query.order_by(Recipe.name).paginate(page=page, per_page=app.config.get('PRODUCTS_PER_PAGE', 10))
        return render_template('admin/recipes/list_recipes.html', recipes_pagination=recipes_pagination, title='Gestion des Recettes')

    @app.route('/admin/recipe/<int:recipe_id>')
    @login_required
    @admin_required
    def view_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id) or abort(404)
        return render_template('admin/recipes/view_recipe.html', recipe=recipe, title=f"Recette: {recipe.name}")

    @app.route('/admin/recipe/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def new_recipe():
        form = RecipeForm(request.form)
        if form.validate_on_submit():
            try:
                recipe = Recipe()
                form.populate_obj(recipe)
                recipe.product_id = form.finished_product.data.id
                db.session.add(recipe)
                db.session.flush()
                for item_data in form.ingredients.data:
                    if item_data.get('product') and item_data.get('quantity_needed'):
                        ingredient = RecipeIngredient(
                            recipe_id=recipe.id, product_id=item_data['product'].id,
                            quantity_needed=item_data['quantity_needed'], unit=item_data['unit'],
                            notes=item_data.get('notes'))
                        db.session.add(ingredient)
                db.session.commit()
                flash(f"Recette '{recipe.name}' créée.", 'success')
                return redirect(url_for('view_recipe', recipe_id=recipe.id))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Erreur création recette: {e}", exc_info=True)
                flash(f"Erreur serveur: {str(e)}", 'danger')
        ingredient_products = Product.query.filter_by(product_type='ingredient').order_by(Product.name).all()
        ingredient_products_json = [{"id": p.id, "name": p.name, "unit": p.unit, "suggested_unit": get_unit_suggestion(p.name, p.unit)} for p in ingredient_products]
        if request.method == 'GET' and not form.ingredients.entries:
            form.ingredients.append_entry()
        return render_template('admin/recipes/recipe_form.html', form=form, title='Nouvelle Recette', ingredient_products_json=ingredient_products_json)

    @app.route('/admin/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id) or abort(404)
        form = RecipeForm(request.form, obj=recipe) if request.method == 'POST' else RecipeForm(obj=recipe)
        if request.method == 'GET':
            form.ingredients.entries.clear()
            for ingredient in recipe.ingredients:
                form.ingredients.append_entry(data={'product': ingredient.product, 'quantity_needed': ingredient.quantity_needed,
                                                     'unit': ingredient.unit, 'notes': ingredient.notes})
            if not form.ingredients.entries:
                form.ingredients.append_entry()
        if form.validate_on_submit():
            try:
                form.populate_obj(recipe)
                recipe.product_id = form.finished_product.data.id
                for old_ingredient in recipe.ingredients:
                    db.session.delete(old_ingredient)
                db.session.flush()
                for item_data in form.ingredients.data:
                    if item_data.get('product') and item_data.get('quantity_needed'):
                        new_ingredient = RecipeIngredient(
                            recipe_id=recipe.id, product_id=item_data['product'].id,
                            quantity_needed=item_data['quantity_needed'], unit=item_data['unit'],
                            notes=item_data.get('notes'))
                        db.session.add(new_ingredient)
                db.session.commit()
                flash(f"Recette '{recipe.name}' modifiée.", 'success')
                return redirect(url_for('view_recipe', recipe_id=recipe.id))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Erreur modification recette {recipe_id}: {e}", exc_info=True)
                flash(f"Erreur serveur: {str(e)}", 'danger')
        ingredient_products = Product.query.filter_by(product_type='ingredient').order_by(Product.name).all()
        ingredient_products_json = [{"id": p.id, "name": p.name, "unit": p.unit, "suggested_unit": get_unit_suggestion(p.name, p.unit)} for p in ingredient_products]
        return render_template('admin/recipes/recipe_form.html', form=form, title=f"Modifier: {recipe.name}", ingredient_products_json=ingredient_products_json, edit_mode=True)

    @app.route('/admin/recipe/<int:recipe_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_recipe(recipe_id):
        recipe = db.session.get(Recipe, recipe_id) or abort(404)
        form = FlaskForm()
        if form.validate_on_submit():
            db.session.delete(recipe)
            db.session.commit()
            flash(f"Recette '{recipe.name}' supprimée.", 'success')
        else:
            flash("Erreur de sécurité.", 'danger')
        return redirect(url_for('list_recipes'))
        
    # == GESTION DES ERREURS ==
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html', title='Accès Interdit'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html', title='Page Non Trouvée'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.error(f"Erreur serveur interne: {error}", exc_info=True)
        return render_template('errors/500.html', title='Erreur Serveur'), 500

    return app


main_app = create_app(os.getenv('FLASK_ENV') or 'default')


@main_app.cli.command("create-admin")
def create_admin():
    username = "admin"
    email = "admin@example.com"
    password = "password123"

    if User.query.filter_by(email=email).first():
        print(f"L'utilisateur avec l'email {email} existe déjà.")
        return

    admin_user = User(username=username, email=email, role='admin')
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()
    print(f"Utilisateur admin '{username}' créé avec succès.")


if __name__ == '__main__':
    main_app.run()