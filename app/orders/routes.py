from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product 
from .forms import OrderForm, OrderStatusForm
from decorators import admin_required
from decimal import Decimal
from datetime import datetime, timezone
# Création du Blueprint 'orders'
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

@orders.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_order():
    form = OrderForm()
    if form.validate_on_submit():
        try:
            # Crée la commande principale avec les données du formulaire
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
                status='pending' # Statut par défaut
            )
            db.session.add(order)
            # 'flush' permet d'obtenir un ID pour la commande avant le commit final
            db.session.flush()

            # Boucle sur les articles soumis avec le formulaire
            for item_data in form.items.data:
                # On ne traite que les lignes où un produit et une quantité valide ont été saisis
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
                    product = item_data['product']
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item_data['quantity'],
                        unit_price=product.price or Decimal('0.00')
                    )
                    db.session.add(order_item)
            
            # Une fois tous les articles ajoutés, on calcule le montant total
            order.calculate_total_amount()
            
            # On sauvegarde tout dans la base de données
            db.session.commit()
            
            flash('Nouvelle commande créée avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la création de la commande: {e}", "danger")
    
    # --- LOGIQUE POUR L'AFFICHAGE DU FORMULAIRE (GET) ---
    
    # Récupérer les produits pour les menus déroulants du formulaire
    products_for_template = Product.query.filter_by(product_type='finished').order_by(Product.name).all()
    
    # Créer une liste de produits qui est "JSON-safe" pour le JavaScript
    products_serializable = [
        {'id': p.id, 'name': p.name, 'price': float(p.price or 0.0)}
        for p in products_for_template
    ]

    return render_template(
        'orders/order_form_multifield.html', 
        form=form, 
        title='Nouvelle Commande',
        # On passe la liste JSON-safe au template
        products_serializable=products_serializable 
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
            # Vider les anciens items avant de peupler
            for item in order.items:
                db.session.delete(item)
            db.session.flush()

            form.populate_obj(order)
            
            # Ajouter les nouveaux items
            for item_data in form.items.data:
                if item_data.get('product') and item_data.get('quantity', 0) > 0:
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
            flash('Commande mise à jour avec succès.', 'success')
            return redirect(url_for('orders.view_order', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de la mise à jour: {e}", "danger")
    
    # Pré-remplir le formulaire avec les items existants pour la méthode GET
    if request.method == 'GET':
        form.items.entries = []
        for item in order.items:
            form.items.append_entry(item)

    # CORRECTION : Il manquait la liste de prix des produits pour la page de modification
    products_for_template = Product.query.filter_by(product_type='finished').order_by(Product.name).all()
    products_serializable = [
        {'id': p.id, 'name': p.name, 'price': float(p.price or 0.0)}
        for p in products_for_template
    ]

    return render_template(
        'orders/order_form_multifield.html', 
        form=form, 
        title=f'Modifier Commande #{order.id}', 
        edit_mode=True,
        products_serializable=products_serializable # CORRECTION : Ajout de la variable manquante
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
            # Vous pouvez ajouter des couleurs en fonction du statut ici
        })
    return render_template('orders/orders_calendar.html', events=events, title="Calendrier des Commandes")