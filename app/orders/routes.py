from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product, Recipe, RecipeIngredient
from .forms import OrderForm, OrderStatusForm, CustomerOrderForm, ProductionOrderForm
from decorators import admin_required
from decimal import Decimal
from datetime import datetime, timezone

orders = Blueprint('orders', __name__)


# ### DEBUT DU BLOC A AJOUTER ###
def check_stock_availability(form_items):
    """
    Vérifie la disponibilité des ingrédients pour une liste d'articles de commande.
    Retourne True si tout est disponible, False sinon, et flashe des messages d'erreur.
    """
    print("\n--- DEBUT DE LA VERIFICATION DE STOCK ---")
    is_sufficient = True
    for item_data in form_items:
        product_id = item_data.get('product')
        quantity_ordered = float(item_data.get('quantity', 0))

        if product_id and quantity_ordered > 0:
            product_fini = Product.query.get(int(product_id))
            print(f"\n[+] Vérification pour le produit fini : {product_fini.name} (Qté: {quantity_ordered})")

            if product_fini and product_fini.recipe_definition:
                recipe = product_fini.recipe_definition
                labo_key = recipe.production_location
                labo_name = "Labo A (Stock Magasin)" if labo_key == 'ingredients_magasin' else "Labo B (Stock Local)"
                print(f"    -> Recette trouvée: '{recipe.name}'. Doit être produit dans: {labo_name} (colonne: {labo_key})")

                for ingredient_in_recipe in recipe.ingredients.all():
                    # --- DEBUT DE LA CORRECTION ---
                    
                    # 1. Calcul de la quantité d'ingrédient nécessaire pour UNE SEULE unité de produit fini
                    # Ex: (4000g de semoule) / (12 galettes) = 333.33g de semoule par galette
                    qty_per_unit = float(ingredient_in_recipe.quantity_needed) / float(recipe.yield_quantity)
                    
                    # 2. Calcul du besoin total pour la commande actuelle
                    # Ex: (333.33g par galette) * (20 galettes commandées) = 6666.6g
                    needed_qty = qty_per_unit * quantity_ordered
                    
                    # --- FIN DE LA CORRECTION ---

                    ingredient_product = ingredient_in_recipe.product
                    
                    print(f"    - Ingrédient requis: {ingredient_product.name}")
                    print(f"      - Quantité par unité de recette: {qty_per_unit:.3f}g") # Log mis à jour
                    print(f"      - Quantité totale nécessaire pour la commande: {needed_qty:.3f}g") # Log mis à jour

                    available_stock = ingredient_product.get_stock_by_location(labo_key)
                    print(f"      - Stock disponible dans '{labo_key}': {available_stock or 0:.3f}g")
                    
                    if not available_stock or available_stock < needed_qty:
                        is_sufficient = False
                        print(f"      - !!! STOCK INSUFFISANT !!!")
                        flash(f"Stock insuffisant pour '{ingredient_product.name}' dans {labo_name}. "
                              f"Besoin: {needed_qty:.3f}g, Dispo: {available_stock or 0:.3f}g", 'danger')
                    else:
                        print(f"      - Stock OK.")
            else:
                print(f"    -> Pas de recette trouvée pour ce produit. Vérification ignorée.")
    
    print(f"\n--- FIN DE LA VERIFICATION. Résultat final : {is_sufficient} ---")
    return is_sufficient
# ### FIN DU BLOC A AJOUTER ###


@orders.route('/customer/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_customer_order():
    form = CustomerOrderForm()
    
    if form.validate_on_submit():
        try:
            # On appelle notre nouvelle fonction de vérification
            stock_is_sufficient = check_stock_availability(form.items.data)
            initial_status = 'in_production' if stock_is_sufficient else 'pending'

            order = Order(
                user_id=current_user.id,
                order_type='customer_order',
                customer_name=form.customer_name.data,
                customer_phone=form.customer_phone.data,
                customer_address=form.customer_address.data,
                delivery_option=form.delivery_option.data,
                due_date=form.due_date.data,
                delivery_cost=form.delivery_cost.data,
                notes=form.notes.data,
                status=initial_status # On utilise le statut calculé
            )

            db.session.add(order)
            db.session.flush()

            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            quantity=item_data['quantity'],
                            unit_price=product.price or Decimal('0.00')
                        )
                        db.session.add(order_item)

            order.calculate_total_amount()
            db.session.commit()

            if not stock_is_sufficient:
                flash('Commande créée mais mise en attente en raison d\'un stock insuffisant.', 'warning')
            else:
                 flash('Commande créée et mise en production. Stock suffisant.', 'success')

            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création commande: {e}", exc_info=True)
            flash(f"Une erreur est survenue lors de la création de la commande: {e}", "danger")

    return render_template(
        'orders/customer_order_form.html',
        form=form,
        title='Nouvelle Commande Client'
    )

@orders.route('/production/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_production_order():
    form = ProductionOrderForm()
    
    if form.validate_on_submit():
        try:
            # On appelle notre nouvelle fonction de vérification
            stock_is_sufficient = check_stock_availability(form.items.data)
            initial_status = 'in_production' if stock_is_sufficient else 'pending'

            order = Order(
                user_id=current_user.id,
                order_type='counter_production_request',
                due_date=form.production_date.data,
                notes=form.production_notes.data,
                status=initial_status, # On utilise le statut calculé
                # Le reste des champs est None ou 0 par défaut
                delivery_cost=Decimal('0.00'),
                total_amount = Decimal('0.00')
            )

            db.session.add(order)
            db.session.flush()

            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            quantity=item_data['quantity'],
                            unit_price=Decimal('0.00')
                        )
                        db.session.add(order_item)
            
            db.session.commit()

            if not stock_is_sufficient:
                flash('Ordre de production créé mais mis en attente en raison d\'un stock insuffisant.', 'warning')
            else:
                flash('Ordre de production créé et mis en production. Stock suffisant.', 'success')
                
            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création ordre production: {e}", exc_info=True)
            flash(f"Une erreur est survenue lors de la création de l'ordre: {e}", "danger")

    return render_template(
        'orders/production_order_form.html',
        form=form,
        title='Nouvel Ordre de Production'
    )

# ... (Le reste du fichier reste identique, je l'omets pour la clarté mais il est dans ton presse-papier)
@orders.route('/')
@login_required
@admin_required
def list_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.order_by(Order.due_date.desc()).paginate(page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10))
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Gestion des Commandes')

@orders.route('/customer')
@login_required
@admin_required
def list_customer_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(order_type='customer_order').order_by(Order.due_date.desc()).paginate(page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10))
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Commandes Client')

@orders.route('/production')
@login_required
@admin_required
def list_production_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(order_type='counter_production_request').order_by(Order.created_at.desc()).paginate(page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10))
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Ordres de Production')

@orders.route('/api/products')
@login_required
@admin_required
def api_products():
    query = request.args.get('q', '')
    products = Product.query.filter(Product.product_type == 'finished', Product.name.ilike(f'%{query}%')).order_by(Product.name).limit(20).all()
    results = []
    for product in products:
        price = float(product.price or 0.0)
        results.append({'id': str(product.id), 'text': f"{product.name} ({price:.2f} DA / {product.unit})", 'name': product.name, 'price': price, 'unit': product.unit})
    return jsonify({'results': results})

@orders.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_order():
    form = OrderForm()
    if form.validate_on_submit():
        try:
            # Note: Cette route devrait aussi utiliser check_stock_availability si elle est utilisée.
            order = Order(user_id=current_user.id, order_type=form.order_type.data, customer_name=form.customer_name.data, customer_phone=form.customer_phone.data, customer_address=form.customer_address.data, delivery_option=form.delivery_option.data, due_date=form.due_date.data, delivery_cost=form.delivery_cost.data, notes=form.notes.data, status='pending')
            db.session.add(order)
            db.session.flush()
            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=item_data['quantity'], unit_price=product.price or Decimal('0.00'))
                        db.session.add(order_item)
            order.calculate_total_amount()
            db.session.commit()
            flash('Nouvelle commande créée avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la création de la commande: {e}", "danger")
    return render_template('orders/order_form_multifield.html', form=form, title='Nouvelle Commande')

@orders.route('/<int:order_id>')
@login_required
@admin_required
def view_order(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    return render_template('orders/view_order.html', order=order, title=f'Détails Commande #{order.id}')

@orders.route('/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    form = OrderForm(obj=order)
    if form.validate_on_submit():
        try:
            # Note: L'édition devrait aussi re-vérifier les stocks.
            for item in order.items:
                db.session.delete(item)
            db.session.flush()
            form.populate_obj(order)
            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = Product.query.get(int(item_data['product']))
                    if product:
                        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=item_data['quantity'], unit_price=product.price or Decimal('0.00'))
                        db.session.add(order_item)
            order.calculate_total_amount()
            db.session.commit()
            flash('Commande mise à jour avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la mise à jour: {e}", "danger")
    if request.method == 'GET':
        form.items.entries = []
        for item in order.items:
            form.items.append_entry({'product': str(item.product_id), 'quantity': item.quantity})
    return render_template('orders/order_form_multifield.html', form=form, title=f'Modifier Commande #{order.id}', edit_mode=True)

@orders.route('/<int:order_id>/edit_status', methods=['GET', 'POST'])
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
        flash('Le statut de la commande a été mis à jour.', 'success')
        return redirect(url_for('orders.view_order', order_id=order.id))
    return render_template('orders/order_status_form.html', form=form, order=order, title='Modifier le Statut')

@orders.route('/calendar')
@login_required
@admin_required
def orders_calendar():
    orders = Order.query.filter(Order.due_date.isnot(None)).all()
    events = []
    for order in orders:
        if order.should_appear_in_calendar():
            events.append({'id': order.id, 'title': f"#{order.id} - {order.customer_name or 'Production'}", 'start': order.due_date.isoformat(), 'url': url_for('orders.view_order', order_id=order.id), 'backgroundColor': '#ffc107' if order.status == 'in_production' else '#6c757d'})
    return render_template('orders/orders_calendar.html', events=events, title="Calendrier des Commandes")