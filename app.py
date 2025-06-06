# app.py

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, url_for, flash, redirect, request, abort, jsonify
from flask.cli import run_command, shell_command, routes_command
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_user, logout_user, login_required
from flask_wtf.csrf import generate_csrf
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone, timedelta 
from sqlalchemy import func 
from markupsafe import Markup, escape 
from config import config_by_name
from forms import (LoginForm, ChangePasswordForm,
                   CategoryForm, ProductForm,
                   StockAdjustmentForm, QuickStockEntryForm,
                   OrderForm, OrderStatusForm)
from models import User, Category, Product, Order, OrderItem
from decorators import admin_required

def create_app(config_name=None):
    app = Flask(__name__)
    
    from extensions import db, migrate, login, csrf
    
    if config_name is None: 
        config_name = os.environ.get('FLASK_ENV') or 'default'
    
    try: 
        app.config.from_object(config_by_name[config_name])
        print(f"--- Chargement de la configuration : {config_name} ---")
    except KeyError: 
        print(f"--- ERREUR : Configuration '{config_name}' non trouvée. Utilisation de 'default'. ---")
        app.config.from_object(config_by_name['default'])
    
    if not hasattr(app.cli, 'run'): 
        app.cli.add_command(run_command)
    if not hasattr(app.cli, 'shell'): 
        app.cli.add_command(shell_command)
    if not hasattr(app.cli, 'routes'): 
        app.cli.add_command(routes_command)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)
    
    login.login_view = 'login'
    login.login_message_category = 'info'
    login.login_message = "Veuillez vous connecter pour accéder à cette page."
    
    @login.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            try: 
                os.mkdir('logs')
            except OSError as e: 
                app.logger.error(f"Erreur création dossier logs : {e}")
        
        log_level_str = app.config.get('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        file_handler = RotatingFileHandler('logs/fee_maison.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info('Démarrage de Fée Maison (mode non-debug)')
    elif app.debug: 
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Démarrage de Fée Maison (mode debug)')
    
    @app.context_processor
    def inject_manual_csrf_token(): 
        return dict(manual_csrf_token=generate_csrf)
    
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None: return ''
        return Markup(escape(s).replace('\n', '<br>\n'))
    
    @app.template_global()
    def current_year():
        return datetime.now().year
    
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
                flash('Connexion réussie !', 'success')
                app.logger.info(f"Utilisateur connecté: {user.username}")
                next_page = request.args.get('next')
                if next_page and not (next_page.startswith('/') or next_page.startswith(request.host_url)): 
                    app.logger.warning(f"Redirection ouverte ignorée: {next_page}")
                    next_page = None
                return redirect(next_page or url_for('dashboard'))
            else: 
                flash('Email ou mot de passe incorrect.', 'danger')
                app.logger.warning(f"Échec connexion pour: {form.email.data}")
        return render_template('login.html', form=form, title='Connexion')
    
    @app.route("/logout")
    @login_required
    def logout(): 
        app.logger.info(f"Utilisateur déconnecté: {current_user.username}")
        logout_user()
        flash('Vous avez été déconnecté.', 'info')
        return redirect(url_for('hello_world'))
    
    @app.route("/dashboard")
    @login_required
    def dashboard():
        now_utc = datetime.now(timezone.utc)
        start_of_month_utc = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        sales_this_month_query = db.session.query(
            func.count(Order.id),
            func.sum(Order.total_amount)
        ).filter(
            Order.order_type == 'customer_order', # Important: Ne compte que les commandes clients
            Order.status == 'completed',
            Order.order_date >= start_of_month_utc,
            Order.order_date <= now_utc
        )
        sales_count_month, total_revenue_month = sales_this_month_query.one()

        sales_count_month = sales_count_month or 0
        total_revenue_month = total_revenue_month or Decimal('0.00')

        active_products_count = Product.query.filter(Product.quantity_in_stock > 0).count() # Ex: produits réellement en stock
        
        total_items_in_stock_result = db.session.query(func.sum(Product.quantity_in_stock)).scalar()
        total_items_in_stock = total_items_in_stock_result if total_items_in_stock_result is not None else 0
        
        dashboard_data = {
            'sales_count_month': sales_count_month,
            'total_revenue_month': total_revenue_month,
            'active_products_count': active_products_count,
            'total_items_in_stock': total_items_in_stock
        }
        return render_template('dashboard.html', title='Tableau de Bord', data=dashboard_data)
    
    @app.route('/account', methods=['GET', 'POST'])
    @login_required
    def account():
        form = ChangePasswordForm()
        if form.validate_on_submit():
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Mot de passe mis à jour avec succès.', 'success')
            app.logger.info(f"Mot de passe MàJ pour: {current_user.username}")
            return redirect(url_for('account'))
        return render_template('account.html', form=form, title='Mon Compte')
    
    @app.route('/admin_dashboard')
    @login_required
    @admin_required
    def admin_dashboard(): 
        return render_template('admin_dashboard.html', title='Tableau de Bord Administrateur')
    
    # == Catégories ==
    @app.route('/categories')
    @login_required
    @admin_required
    def list_categories(): 
        categories = Category.query.order_by(Category.name).all()
        return render_template('categories/list_categories.html', categories=categories, title='Catégories')
    
    @app.route('/category/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def new_category():
        form = CategoryForm()
        if form.validate_on_submit():
            name = form.name.data.strip()
            description = form.description.data.strip() if form.description.data else None
            if Category.query.filter_by(name=name).first(): 
                flash(f"Une catégorie nommée '{name}' existe déjà.", 'danger')
            else: 
                category = Category(name=name, description=description)
                db.session.add(category)
                db.session.commit()
                flash('Nouvelle catégorie ajoutée avec succès !', 'success')
                app.logger.info(f"Nouvelle catégorie créée: {category.name} par {current_user.username}")
                return redirect(url_for('list_categories'))
        return render_template('categories/category_form.html', form=form, title='Nouvelle Catégorie', legend='Nouvelle Catégorie')
    
    @app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_category(category_id):
        category = db.session.get(Category, category_id) or abort(404)
        form = CategoryForm(obj=category)
        if form.validate_on_submit():
            new_name = form.name.data.strip()
            new_description = form.description.data.strip() if form.description.data else None
            if new_name != category.name and Category.query.filter(Category.id != category_id, Category.name == new_name).first(): 
                flash(f"Une catégorie nommée '{new_name}' existe déjà.", 'danger')
                return render_template('categories/category_form.html', form=form, category=category, title='Modifier la Catégorie', legend=f'Modifier : {category.name}')
            category.name = new_name
            category.description = new_description
            db.session.commit()
            flash('Catégorie mise à jour avec succès !', 'success')
            app.logger.info(f"Catégorie modifiée: {category.name} par {current_user.username}")
            return redirect(url_for('list_categories'))
        return render_template('categories/category_form.html', form=form, category=category, title='Modifier la Catégorie', legend=f'Modifier : {category.name}')
    
    @app.route('/category/<int:category_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_category(category_id):
        category = db.session.get(Category, category_id) or abort(404)
        if category.products.count() > 0 : 
            flash('Cette catégorie contient des produits et ne peut pas être supprimée.', 'danger')
        else: 
            db.session.delete(category)
            db.session.commit()
            flash('Catégorie supprimée avec succès !', 'success')
        return redirect(url_for('list_categories'))
    
    # == Produits ==
    @app.route('/products')
    @login_required
    @admin_required
    def list_products():
        page = request.args.get('page', 1, type=int)
        products_pagination = Product.query.order_by(Product.name).paginate(page=page, per_page=10)
        return render_template('products/list_products.html', products_pagination=products_pagination, title='Produits')
    
    @app.route('/product/<int:product_id>')
    @login_required
    def view_product(product_id):
        product = db.session.get(Product, product_id) or abort(404)
        return render_template('products/view_product.html', product=product, title=product.name)
    
    @app.route('/product/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def new_product_route():
        form = ProductForm()
        if form.validate_on_submit():
            name = form.name.data.strip()
            sku = form.sku.data.strip() if form.sku.data else None
            description = form.description.data.strip() if form.description.data else None
            if Product.query.filter_by(name=name).first():
                flash(f"Un produit nommé '{name}' existe déjà.", 'danger')
            else:
                product_obj = Product(
                    name=name, description=description, product_type=form.product_type.data, 
                    unit=form.unit.data, price=form.price.data, cost_price=form.cost_price.data, 
                    sku=sku, quantity_in_stock=form.quantity_in_stock.data, category_id=form.category.data.id)
                db.session.add(product_obj)
                db.session.commit()
                flash('Nouveau produit ajouté avec succès !', 'success')
                app.logger.info(f"Nouveau produit créé: {product_obj.name} (SKU: {product_obj.sku or 'N/A'}) par {current_user.username}")
                return redirect(url_for('list_products'))
        return render_template('products/product_form.html', form=form, title='Nouveau Produit', legend='Ajouter un Produit')
    
    @app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_product(product_id):
        product = db.session.get(Product, product_id) or abort(404)
        form = ProductForm(obj=product)
        if form.validate_on_submit():
            new_name = form.name.data.strip()
            new_sku = form.sku.data.strip() if form.sku.data else None
            new_description = form.description.data.strip() if form.description.data else None
            if new_name != product.name and Product.query.filter(Product.id != product_id, Product.name == new_name).first(): 
                flash(f"Un produit nommé '{new_name}' existe déjà.", 'danger')
            else:
                product.name = new_name
                product.description = new_description
                product.product_type = form.product_type.data
                product.unit = form.unit.data
                product.price = form.price.data
                product.cost_price = form.cost_price.data
                product.sku = new_sku
                product.quantity_in_stock = form.quantity_in_stock.data
                product.category_id = form.category.data.id
                db.session.commit()
                flash('Produit mis à jour avec succès !', 'success')
                app.logger.info(f"Produit modifié: {product.name} (SKU: {product.sku or 'N/A'}) par {current_user.username}")
                return redirect(url_for('list_products'))
        return render_template('products/product_form.html', form=form, title='Modifier Produit', legend=f'Modifier: {product.name}', product=product)
    
    @app.route('/product/<int:product_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_product(product_id):
        product = db.session.get(Product, product_id) or abort(404)
        db.session.delete(product)
        db.session.commit()
        flash('Produit supprimé avec succès.', 'success')
        app.logger.info(f"Produit supprimé: {product.name} par {current_user.username}")
        return redirect(url_for('list_products'))
    
    # --- ROUTES POUR LA GESTION DU STOCK ---
    @app.route('/admin/stock_adjustment', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def stock_adjustment():
        form = StockAdjustmentForm()
        if form.validate_on_submit():
            product_obj = form.product.data # Renommé pour éviter conflit avec module product
            quantity_change = form.quantity.data
            reason = form.reason.data.strip() if form.reason.data else "Ajustement manuel par admin"
            old_stock = product_obj.quantity_in_stock
            new_stock = old_stock + quantity_change
            if new_stock < 0: 
                flash(f'Ajustement impossible : stock de "{product_obj.name}" deviendrait négatif ({new_stock}). Stock actuel : {old_stock}.', 'danger')
            else:
                product_obj.quantity_in_stock = new_stock
                db.session.commit()
                log_msg = f"Ajustement stock {product_obj.name} ({product_obj.sku or 'N/A'}): {old_stock} -> {new_stock} (Chg: {quantity_change}). Raison: {reason}. Par: {current_user.username}"
                app.logger.info(log_msg)
                flash(f'Stock de "{product_obj.name}" ajusté à {new_stock}.', 'success')
                return redirect(url_for('stock_adjustment'))
        return render_template('admin/stock_adjustment_form.html', form=form, title='Ajustement de Stock Admin')
    
    @app.route('/quick_stock_entry', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def quick_stock_entry():
        form = QuickStockEntryForm()
        if form.validate_on_submit():
            product_obj = form.product.data # Renommé
            quantity_received = form.quantity_received.data
            old_stock = product_obj.quantity_in_stock
            product_obj.quantity_in_stock += quantity_received
            db.session.commit()
            app.logger.info(f'Réception magasin (rapide): {product_obj.name} - {old_stock} -> {product_obj.quantity_in_stock} (+{quantity_received}) par {current_user.username}')
            flash(f'Réception: +{quantity_received} "{product_obj.name}". Stock total: {product_obj.quantity_in_stock}.', 'success')
            return redirect(url_for('quick_stock_entry'))
        return render_template('admin/quick_stock_entry.html', form=form, title='Réception Magasin Rapide')
    
    @app.route('/admin/stock_overview')
    @login_required
    @admin_required
    def stock_overview():
        low_stock_threshold = 5
        low_stock_products = Product.query.filter(Product.quantity_in_stock > 0, Product.quantity_in_stock < low_stock_threshold).order_by(Product.quantity_in_stock).all()
        out_of_stock_products = Product.query.filter(Product.quantity_in_stock == 0).order_by(Product.name).all()
        total_products_count = Product.query.count()
        total_stock_value = Decimal(0.0)
        all_products_for_value = Product.query.filter(Product.quantity_in_stock > 0).all()
        for product_item in all_products_for_value:
            cost = Decimal(0.0)
            if product_item.cost_price is not None and product_item.cost_price > 0: 
                cost = product_item.cost_price
            elif product_item.product_type == 'finished' and product_item.price is not None: 
                cost = product_item.price * Decimal('0.7')
            if cost > 0: 
                total_stock_value += (cost * Decimal(product_item.quantity_in_stock))
        return render_template('admin/stock_overview.html',
                             low_stock_products=low_stock_products, out_of_stock_products=out_of_stock_products,
                             total_products_count=total_products_count, total_stock_value=total_stock_value,
                             title='Vue d\'ensemble du Stock')
    
    # == Commandes Client ==
    @app.route('/admin/orders')
    @login_required
    @admin_required
    def list_orders():
        page = request.args.get('page', 1, type=int)
        orders_pagination = Order.query.order_by(Order.order_date.desc()).paginate(page=page, per_page=10)
        return render_template('admin/orders/list_orders.html', orders_pagination=orders_pagination, title='Gestion des Commandes Clients')
    
    @app.route('/admin/order/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def new_order():
        form = OrderForm()
        products_for_template = Product.query.filter_by(product_type='finished').order_by(Product.name).all()
        products_serializable = [{'id': p.id, 'name': p.name, 'price': float(p.price) if p.price else 0.0} for p in products_for_template]
        
        if request.method == 'POST':
            if form.validate_on_submit():
                try:
                    valid_items_from_form = [item for item in form.items.data if item.get('product') and item.get('quantity') and item.get('quantity') > 0]
                    if not valid_items_from_form:
                        flash("Veuillez ajouter au moins un article valide à la commande.", "danger")
                        return render_template('admin/orders/order_form_multifield.html',
                                             form=form, products_for_select=products_for_template,
                                             products_serializable=products_serializable,
                                             title='Nouvelle Commande', legend='Créer une Commande')

                    order_type_data = form.order_type.data
                    customer_name_data = form.customer_name.data.strip() if form.customer_name.data else None
                    customer_phone_data = form.customer_phone.data.strip() if form.customer_phone.data else None
                    customer_address_data = form.customer_address.data.strip() if form.customer_address.data else None
                    delivery_option_data = form.delivery_option.data
                    delivery_cost_data = form.delivery_cost.data if form.delivery_cost.data is not None else Decimal('0.00')
                    
                    if order_type_data == 'counter_production_request':
                        customer_name_data = "Production Comptoir"
                        customer_phone_data = None
                        customer_address_data = None
                        delivery_option_data = 'pickup' 
                        delivery_cost_data = Decimal('0.00')
                    
                    order = Order(
                        order_type=order_type_data, user_id=current_user.id,
                        customer_name=customer_name_data, customer_phone=customer_phone_data,
                        customer_address=customer_address_data,
                        notes=form.notes.data.strip() if form.notes.data else None,
                        status='pending', delivery_option=delivery_option_data,
                        due_date=form.due_date.data, delivery_cost=delivery_cost_data
                    )
                    
                    for item_data_dict in valid_items_from_form: # Renommé pour éviter conflit
                        product_obj = item_data_dict['product']
                        quantity = item_data_dict['quantity']
                        price_at_order = product_obj.price if product_obj.price is not None else Decimal('0.00')
                        order_item = OrderItem(product_id=product_obj.id, quantity=quantity, price_at_order=price_at_order)
                        order.items.append(order_item)
                    
                    db.session.add(order)
                    db.session.flush() 
                    order.calculate_total_amount()
                    db.session.commit()
                    
                    flash(f'{order.get_order_type_display()} #{order.id} créée avec succès ! ({len(order.items.all())} articles)', 'success')
                    app.logger.info(f'Commande créée: #{order.id} avec {len(order.items.all())} articles par {current_user.username}')
                    return redirect(url_for('view_order', order_id=order.id))
                    
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f'Erreur création commande: {str(e)}', exc_info=True)
                    flash(f'Erreur lors de la création de la commande: {str(e)}', 'danger')
            else: 
                flash("Veuillez corriger les erreurs dans le formulaire.", "warning")

        if request.method == 'GET' and not form.items.data:
            form.items.append_entry()
        
        return render_template('admin/orders/order_form_multifield.html',
                             form=form, products_for_select=products_for_template,
                             products_serializable=products_serializable,
                             title='Nouvelle Commande Multi-Produits', legend='Créer une Commande')
    
    @app.route('/admin/order/<int:order_id>')
    @login_required
    @admin_required
    def view_order(order_id):
        order = db.session.get(Order, order_id) or abort(404)
        return render_template('admin/orders/view_order.html', order=order, title=f'Détails Commande #{order.id}')
    
    @app.route('/admin/order/<int:order_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_order(order_id):
        order = db.session.get(Order, order_id) or abort(404)
        products_for_template = Product.query.filter_by(product_type='finished').order_by(Product.name).all()
        products_serializable = [{'id': p.id, 'name': p.name, 'price': float(p.price) if p.price else 0.0} for p in products_for_template]
        
        form = OrderForm(request.form if request.method == 'POST' else None, obj=order if request.method == 'GET' else None)

        if request.method == 'GET':
            form.items.entries.clear()
            for order_item in order.items:
                form.items.append_entry({'product': order_item.product, 'quantity': order_item.quantity})
            if not form.items.entries: form.items.append_entry()
        
        if form.validate_on_submit():
            try:
                valid_items_from_form = [item for item in form.items.data if item.get('product') and item.get('quantity') and item.get('quantity') > 0]
                if not valid_items_from_form:
                    flash("Veuillez ajouter au moins un article valide à la commande.", "danger")
                    return render_template('admin/orders/order_form_multifield.html',
                                         form=form, products_for_select=products_for_template,
                                         products_serializable=products_serializable,
                                         title=f'Modifier Commande #{order.id}', legend=f'Modifier Commande #{order.id}',
                                         edit_mode=True, order=order)
                
                order.order_type = form.order_type.data
                order.customer_name = form.customer_name.data.strip() if form.customer_name.data else None
                order.customer_phone = form.customer_phone.data.strip() if form.customer_phone.data else None
                order.customer_address = form.customer_address.data.strip() if form.customer_address.data else None
                order.delivery_option = form.delivery_option.data
                order.due_date = form.due_date.data
                order.delivery_cost = form.delivery_cost.data if form.delivery_cost.data is not None else Decimal('0.00')
                order.notes = form.notes.data.strip() if form.notes.data else None

                if order.order_type == 'counter_production_request':
                    order.customer_name = "Production Comptoir"
                    order.customer_phone = None
                    order.customer_address = None
                    order.delivery_option = 'pickup'
                    order.delivery_cost = Decimal('0.00')

                for old_item in order.items.all(): db.session.delete(old_item)
                db.session.flush()

                new_items_count = 0
                for item_data_dict in valid_items_from_form: # Renommé
                    product_obj = item_data_dict['product']
                    quantity = item_data_dict['quantity']
                    price_at_order = product_obj.price if product_obj.price is not None else Decimal('0.00')
                    new_order_item = OrderItem(order_id=order.id, product_id=product_obj.id, quantity=quantity, price_at_order=price_at_order)
                    db.session.add(new_order_item)
                    new_items_count += 1
                
                db.session.flush()
                order.calculate_total_amount()
                db.session.commit()
                
                flash(f'Commande #{order.id} modifiée avec succès ! ({new_items_count} articles)', 'success')
                app.logger.info(f'Commande #{order.id} modifiée par {current_user.username}')
                return redirect(url_for('view_order', order_id=order.id))
                
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Erreur modif commande #{order.id}: {str(e)}', exc_info=True)
                flash(f'Erreur lors de la modification: {str(e)}', 'danger')
        
        if request.method == 'POST' and not form.validate_on_submit():
             flash("Veuillez corriger les erreurs dans le formulaire.", "warning")
             if not form.items.entries: form.items.append_entry()

        return render_template('admin/orders/order_form_multifield.html',
                             form=form, products_for_select=products_for_template,
                             products_serializable=products_serializable,
                             title=f'Modifier Commande #{order.id}', legend=f'Modifier Commande #{order.id}',
                             edit_mode=True, order=order)
    
    @app.route('/admin/order/<int:order_id>/edit_status', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_order_status(order_id):
        order = db.session.get(Order, order_id) or abort(404)
        form = OrderStatusForm(obj=order)
        if form.validate_on_submit():
            try:
                old_status_display = order.get_status_display()
                order.status = form.status.data
                if form.notes.data and form.notes.data.strip():
                    new_note = f"MàJ Statut ({datetime.now(timezone.utc).strftime('%d/%m %H:%M')} par {current_user.username}): {order.get_status_display()}.\nNote: {form.notes.data.strip()}"
                    order.notes = (order.notes + "\n---\n" if order.notes and order.notes.strip() else "") + new_note
                db.session.commit()
                flash(f'Statut de la commande #{order.id} mis à jour vers : {order.get_status_display()}', 'success')
                app.logger.info(f"Statut commande #{order.id} MàJ: {old_status_display} -> {order.get_status_display()} par {current_user.username}")
                return redirect(url_for('view_order', order_id=order.id))
            except Exception as e: 
                db.session.rollback()
                app.logger.error(f"Erreur MàJ statut commande #{order.id}: {e}", exc_info=True)
                flash('Erreur serveur lors de la mise à jour du statut.', 'danger')
        return render_template('admin/orders/order_status_form.html',
                             form=form, order=order, title=f'Modifier Statut Commande #{order.id}',
                             legend=f'Modifier Statut : Commande #{order.id}')
    
    @app.route('/admin/orders/calendar')
    @login_required
    @admin_required
    def orders_calendar():
        try:
            orders_with_due_date = Order.query.filter(Order.due_date.isnot(None)).order_by(Order.due_date).all()
            events = []
            default_text_color = '#ffffff'; dark_text_color = '#212529'
            status_colors = {
                'pending':          {'background': '#0d6efd', 'text': default_text_color}, 
                'pending_comptoir': {'background': '#198754', 'text': default_text_color}, 
                'ready_at_shop':    {'background': '#6c757d', 'text': default_text_color}, 
                'completed':        {'background': '#adb5bd', 'text': dark_text_color},    
                'cancelled':        {'background': '#dc3545', 'text': default_text_color}, 
                'out_for_delivery': {'background': '#fd7e14', 'text': default_text_color}, 
                'awaiting_payment': {'background': '#ffc107', 'text': dark_text_color}     
            }
            default_color_customer = status_colors['pending']
            default_color_counter = status_colors['pending_comptoir']

            for order_obj in orders_with_due_date: # Renommé pour éviter conflit
                first_item = order_obj.items.first() if order_obj.items else None
                title_parts = []
                if order_obj.order_type == 'customer_order':
                    title_parts.append(f"Cli: {order_obj.customer_name or 'N/A'}")
                    color_info = status_colors.get(order_obj.status, default_color_customer)
                else: 
                    title_parts.append("Comptoir")
                    current_status_key = order_obj.status if order_obj.status != 'pending' else 'pending_comptoir'
                    color_info = status_colors.get(current_status_key, default_color_counter)
                
                title_parts.append(f"#{order_obj.id}")
                if first_item and first_item.product: title_parts.append(f"({first_item.product.name} x{first_item.quantity})")
                title = " - ".join(title_parts)
                
                event = {
                    'id': str(order_obj.id), 'title': title, 'start': order_obj.due_date.isoformat(),
                    'url': url_for('view_order', order_id=order_obj.id),
                    'backgroundColor': color_info['background'], 'borderColor': color_info['background'],
                    'textColor': color_info['text'], 'allDay': False, 
                    'extendedProps': {
                        'orderType': order_obj.get_order_type_display(), 'status': order_obj.get_status_display(),
                        'totalAmount': float(order_obj.total_amount or 0),
                        'customerName': order_obj.customer_name if order_obj.order_type == 'customer_order' else 'Production Comptoir',
                        'productName': first_item.product.name if first_item and first_item.product else 'N/A',
                        'quantity': first_item.quantity if first_item else 0}}
                events.append(event)
            
            app.logger.info(f'Calendrier: {len(events)} événements générés.')
            return render_template('admin/orders/orders_calendar.html',
                                 events=events, title='Calendrier des Commandes et Productions',
                                 total_orders_on_calendar=len(events))
        except Exception as e:
            app.logger.error(f"Erreur génération calendrier: {e}", exc_info=True)
            flash("Erreur chargement calendrier.", "danger")
            return redirect(url_for('list_orders'))
    
    @app.errorhandler(403)
    def forbidden_error(error): return render_template('errors/403.html', title='Accès Interdit'), 403
    @app.errorhandler(404)
    def not_found_error(error): return render_template('errors/404.html', title='Page Non Trouvée'), 404
    @app.errorhandler(500)
    def internal_server_error(error): 
        db.session.rollback()
        app.logger.error(f"Erreur serveur interne: {error}", exc_info=True)
        return render_template('errors/500.html', title='Erreur Serveur'), 500
    
    return app

main_app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == '__main__':
    main_app.run()