from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product
from .forms import OrderForm, OrderStatusForm, CustomerOrderForm, ProductionOrderForm
from decorators import admin_required
from decimal import Decimal
from datetime import datetime, timezone

orders = Blueprint('orders', __name__)

@orders.route('/')
@login_required
@admin_required
def list_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.order_by(Order.due_date.desc()).paginate(
        page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10)
    )
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Gestion des Commandes')

@orders.route('/customer')
@login_required
@admin_required
def list_customer_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(order_type='customer_order').order_by(Order.due_date.desc()).paginate(
        page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10)
    )
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Commandes Client')

@orders.route('/production')
@login_required
@admin_required
def list_production_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(order_type='counter_production_request').order_by(Order.created_at.desc()).paginate(
        page=page, per_page=current_app.config.get('ORDERS_PER_PAGE', 10)
    )
    return render_template('orders/list_orders.html', orders_pagination=pagination, title='Ordres de Production')

@orders.route('/api/products')
@login_required
@admin_required
def api_products():
    query = request.args.get('q', '')
    products = Product.query.filter(
        Product.product_type == 'finished',
        Product.name.ilike(f'%{query}%')
    ).order_by(Product.name).limit(20).all()
    
    results = []
    for product in products:
        price = float(product.price or 0.0)
        results.append({
            'id': str(product.id),
            'text': f"{product.name} ({price:.2f} DA / {product.unit})",
            'name': product.name,
            'price': price,
            'unit': product.unit
        })
    
    return jsonify({'results': results})

@orders.route('/customer/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_customer_order():
    form = CustomerOrderForm()
    
    if form.validate_on_submit():
        try:
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
                status='pending'
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

            flash('Commande client créée avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
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
            order = Order(
                user_id=current_user.id,
                order_type='counter_production_request',
                customer_name=None,
                customer_phone=None,
                customer_address=None,
                delivery_option=None,
                due_date=form.production_date.data,
                delivery_cost=Decimal('0.00'),
                notes=form.production_notes.data,
                status='pending'
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
                            unit_price=Decimal('0.00')  # Pas de prix pour production
                        )
                        db.session.add(order_item)

            order.total_amount = Decimal('0.00')  # Pas de montant pour production
            db.session.commit()

            flash('Ordre de production créé avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la création de l'ordre: {e}", "danger")

    return render_template(
        'orders/production_order_form.html',
        form=form,
        title='Nouvel Ordre de Production'
    )

@orders.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_order():
    form = OrderForm()
    
    if form.validate_on_submit():
        try:
            order = Order(
                user_id=current_user.id,
                order_type=form.order_type.data,
                customer_name=form.customer_name.data,
                customer_phone=form.customer_phone.data,
                customer_address=form.customer_address.data,
                delivery_option=form.delivery_option.data,
                due_date=form.due_date.data,
                delivery_cost=form.delivery_cost.data,
                notes=form.notes.data,
                status='pending'
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

            flash('Nouvelle commande créée avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la création de la commande: {e}", "danger")

    return render_template(
        'orders/order_form_multifield.html',
        form=form,
        title='Nouvelle Commande'
    )

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
            for item in order.items:
                db.session.delete(item)
            db.session.flush()

            form.populate_obj(order)
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

            flash('Commande mise à jour avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la mise à jour: {e}", "danger")

    if request.method == 'GET':
        form.items.entries = []
        for item in order.items:
            form.items.append_entry({
                'product': str(item.product_id),
                'quantity': item.quantity
            })

    return render_template(
        'orders/order_form_multifield.html',
        form=form,
        title=f'Modifier Commande #{order.id}',
        edit_mode=True
    )

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
        events.append({
            'id': order.id,
            'title': f"#{order.id} - {order.customer_name}",
            'start': order.due_date.isoformat(),
            'url': url_for('orders.view_order', order_id=order.id)
        })
    return render_template('orders/orders_calendar.html', events=events, title="Calendrier des Commandes")
