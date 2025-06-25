"""

Routes pour la gestion des achats fournisseurs avec système d'unités et paiement

Module: app/purchases/routes.py

Auteur: ERP Fée Maison

"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from extensions import db
from .models import Purchase, PurchaseItem, PurchaseStatus, PurchaseUrgency
from .forms import (PurchaseForm, MarkAsPaidForm, PurchaseApprovalForm, PurchaseReceiptForm,
PurchaseSearchForm, QuickPurchaseForm, PurchaseReceiptItemForm)
from decorators import admin_required
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import json
import pytz

# Import du blueprint depuis __init__.py
from . import bp as purchases

# Fonction helper pour récupérer les modèles principaux sans circularité
def get_main_models():
    """Fonction helper pour importer Product, User et Unit sans circularité"""
    import sys
    if 'models' in sys.modules:
        models_module = sys.modules['models']
        return models_module.Product, models_module.User, models_module.Unit
    else:
        # Fallback import si nécessaire
        from models import Product, User, Unit
        return Product, User, Unit

# ==================== ROUTES PRINCIPALES CRUD ====================

@purchases.route('/')
@login_required
def list_purchases():
    """Liste de tous les achats avec filtres et statut paiement"""
    Product, User, Unit = get_main_models()
    form = PurchaseSearchForm()
    
    # Construction de la requête de base
    query = Purchase.query
    
    # ✅ NOUVEAU : Filtre par statut de paiement
    payment_filter = request.args.get('payment_status', 'all')
    if payment_filter == 'unpaid':
        query = query.filter(Purchase.is_paid == False)
    elif payment_filter == 'paid':
        query = query.filter(Purchase.is_paid == True)

    # Filtres existants
    if form.validate_on_submit():
        if form.search_term.data:
            search = f"%{form.search_term.data}%"
            query = query.filter(or_(
                Purchase.reference.ilike(search),
                Purchase.supplier_name.ilike(search),
                Purchase.notes.ilike(search)
            ))
        if form.status_filter.data != 'all':
            query = query.filter(Purchase.status == PurchaseStatus(form.status_filter.data))
        if form.urgency_filter.data != 'all':
            query = query.filter(Purchase.urgency == PurchaseUrgency(form.urgency_filter.data))
        if form.supplier_filter.data:
            supplier_search = f"%{form.supplier_filter.data}%"
            query = query.filter(Purchase.supplier_name.ilike(supplier_search))

    # Pagination et tri
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PURCHASES_PER_PAGE', 20)
    purchases = query.order_by(desc(Purchase.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # ✅ NOUVEAU : Statistiques avec paiements
    stats = {
        'total_purchases': Purchase.query.count(),
        'pending_approval': Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
        ).count(),
        'unpaid_purchases': Purchase.query.filter(Purchase.is_paid == False).count(),
        'paid_purchases': Purchase.query.filter(Purchase.is_paid == True).count(),
        'overdue': len([p for p in Purchase.query.all() if p.is_overdue()])
    }

    # Variables pour le template
    suppliers_list = db.session.query(Purchase.supplier_name).distinct().all()
    suppliers_list = [s[0] for s in suppliers_list if s[0]]

    return render_template(
        'purchases/list_purchases.html',
        title="Gestion des Achats",
        purchases=purchases,
        form=form,
        stats=stats,
        total_purchases=stats['total_purchases'],
        pending_purchases=stats['pending_approval'],
        unpaid_purchases=stats['unpaid_purchases'], # ✅ NOUVEAU
        paid_purchases=stats['paid_purchases'], # ✅ NOUVEAU
        total_amount_month=0,
        suppliers_count=len(suppliers_list),
        suppliers_list=suppliers_list,
        pagination=purchases,
        current_payment_filter=payment_filter # ✅ NOUVEAU
    )

@purchases.route('/new', methods=['GET', 'POST'])
@login_required
def new_purchase():
    """Création d'un nouveau bon d'achat avec PMP et gestion des consommables."""
    Product, User, Unit = get_main_models()

    if request.method == 'POST':
        form = PurchaseForm(request.form)
    else:
        form = PurchaseForm()

    if form.validate_on_submit():
        # ... (le début de la fonction reste identique)
        local_tz = pytz.timezone('Europe/Paris')
        naive_date = form.requested_date.data
        aware_date = local_tz.localize(naive_date)
        purchase = Purchase(
            # ... (tous les champs de l'objet Purchase)
            supplier_name=form.supplier_name.data,
            supplier_contact=form.supplier_contact.data,
            supplier_phone=form.supplier_phone.data,
            supplier_email=form.supplier_email.data,
            supplier_address=form.supplier_address.data,
            expected_delivery_date=form.expected_delivery_date.data,
            urgency=PurchaseUrgency(form.urgency.data),
            payment_terms=form.payment_terms.data,
            shipping_cost=form.shipping_cost.data or 0.0,
            tax_amount=form.tax_amount.data or 0.0,
            notes=form.notes.data,
            internal_notes=form.internal_notes.data,
            terms_conditions=form.terms_conditions.data,
            requested_date=aware_date,
            requested_by_id=current_user.id,
            is_paid=False,
            status=PurchaseStatus.RECEIVED
        )
        db.session.add(purchase)
        db.session.flush()

        items_added = 0
        product_ids = request.form.getlist('items[][product_id]')
        quantities = request.form.getlist('items[][quantity_ordered]')
        prices = request.form.getlist('items[][unit_price]')
        unit_ids = request.form.getlist('items[][unit]')
        stock_locations = request.form.getlist('items[][stock_location]')
        
        for i in range(len(product_ids)):
            try:
                product_id = int(product_ids[i])
                product = Product.query.get(product_id)
                quantity = float(quantities[i])
                price_per_unit_achat = float(prices[i])
                unit_id = int(unit_ids[i])
                
                if not (product and quantity > 0 and price_per_unit_achat >= 0 and unit_id):
                    continue
                
                unit_object = Unit.query.get(unit_id)
                if not unit_object:
                    continue

                quantity_in_base_unit = unit_object.to_base_unit(quantity)
                
                # ### DEBUT DE LA CORRECTION POUR CONSOMMABLES ###
                
                # Si c'est un consommable, on le met dans le bon stock et on ne calcule pas le PMP.
                if product.product_type == 'consommable':
                    stock_location = 'consommables'
                    product.update_stock_by_location(stock_location, quantity_in_base_unit)
                    print(f"CONSOMMABLE: Ajout de {quantity_in_base_unit} de {product.name} au stock consommables.")
                
                # Si c'est un ingrédient, on fait le calcul PMP.
                elif product.product_type == 'ingredient':
                    stock_location = stock_locations[i]
                    price_per_base_unit = price_per_unit_achat / float(unit_object.conversion_factor) if unit_object.conversion_factor > 0 else 0
                    purchase_value = quantity_in_base_unit * price_per_base_unit

                    product.total_stock_value = float(product.total_stock_value or 0.0) + purchase_value
                    product.update_stock_by_location(stock_location, quantity_in_base_unit)
                    
                    new_total_stock_qty = product.total_stock_all_locations
                    if new_total_stock_qty > 0:
                        product.cost_price = product.total_stock_value / new_total_stock_qty
                    else:
                        product.cost_price = price_per_base_unit
                    
                    print(f"INGREDIENT: {product.name} - Nouveau PMP: {product.cost_price}")

                # ### FIN DE LA CORRECTION ###

                # On crée l'item d'achat dans tous les cas pour l'historique
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    quantity_ordered=quantity_in_base_unit,
                    unit_price=price_per_unit_achat / float(unit_object.conversion_factor) if unit_object.conversion_factor > 0 else 0,
                    original_quantity=quantity,
                    original_unit_id=unit_id,
                    original_unit_price=price_per_unit_achat,
                    stock_location=stock_location
                )
                db.session.add(purchase_item)
                items_added += 1

            except (ValueError, IndexError, TypeError) as e:
                current_app.logger.error(f"Erreur traitement item PMP: {e}", exc_info=True)
                continue

        # ... (le reste de la fonction reste identique)
        if items_added == 0:
            db.session.rollback()
            flash('Aucun article valide. Le bon d\'achat a été annulé.', 'danger')
            return redirect(url_for('purchases.new_purchase'))

        purchase.calculate_totals()
        db.session.commit()
        
        flash(f'Bon d\'achat {purchase.reference} créé. Le stock et le coût moyen pondéré ont été mis à jour.', 'success')
        return redirect(url_for('purchases.view_purchase', id=purchase.id))

    available_products = Product.query.filter(Product.product_type.in_(['ingredient', 'consommable'])).all()
    available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()

    return render_template('purchases/new_purchase.html', form=form, title='Nouveau Bon d\'Achat',
                           available_products=available_products, available_units=available_units)

@purchases.route('/<int:id>')
@login_required
def view_purchase(id):
    """Affichage détaillé d'un bon d'achat avec unités et paiement"""
    purchase = Purchase.query.get_or_404(id)
    if not current_user.is_admin and purchase.requested_by_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation de voir ce bon d\'achat.', 'danger')
        return redirect(url_for('purchases.list_purchases'))
    return render_template(
        'purchases/view_purchase.html',
        title=f"Bon d'Achat {purchase.reference}",
        purchase=purchase
    )

@purchases.route('/<int:id>/mark_paid', methods=['GET', 'POST'])
@login_required
@admin_required
def mark_as_paid(id):
    """Marquer un bon d'achat comme payé"""
    purchase = Purchase.query.get_or_404(id)
    if purchase.is_paid:
        flash('Ce bon d\'achat est déjà marqué comme payé.', 'info')
        return redirect(url_for('purchases.view_purchase', id=id))

    form = MarkAsPaidForm()
    if form.validate_on_submit():
        purchase.is_paid = True
        purchase.payment_date = form.payment_date.data
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} marqué comme payé le {form.payment_date.data.strftime("%d/%m/%Y")}.', 'success')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    return render_template(
        'purchases/mark_paid.html',
        purchase=purchase,
        form=form,
        title=f'Marquer comme Payé - {purchase.reference}'
    )

@purchases.route('/<int:id>/mark_unpaid', methods=['POST'])
@login_required
@admin_required
def mark_as_unpaid(id):
    """Marquer un bon d'achat comme non payé"""
    purchase = Purchase.query.get_or_404(id)
    purchase.is_paid = False
    purchase.payment_date = None
    db.session.commit()
    flash(f'Bon d\'achat {purchase.reference} marqué comme non payé.', 'success')
    return redirect(url_for('purchases.view_purchase', id=id))

@purchases.route('/<int:id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_purchase(id):
    """Annuler un bon d'achat et reverser le stock"""
    purchase = Purchase.query.get_or_404(id)
    if purchase.status == PurchaseStatus.CANCELLED:
        flash('Ce bon d\'achat est déjà annulé.', 'info')
        return redirect(url_for('purchases.view_purchase', id=id))

    if purchase.status == PurchaseStatus.RECEIVED:
        stock_reversions = []
        for item in purchase.items:
            if item.product:
                if item.stock_location == 'ingredients_magasin':
                    item.product.stock_ingredients_magasin -= float(item.quantity_ordered)
                    stock_location_display = "Stock Magasin"
                elif item.stock_location == 'ingredients_local':
                    item.product.stock_ingredients_local -= float(item.quantity_ordered)
                    stock_location_display = "Stock Local"
                elif item.stock_location == 'comptoir':
                    item.product.stock_comptoir -= float(item.quantity_ordered)
                    stock_location_display = "Stock Comptoir"
                elif item.stock_location == 'consommables':
                    item.product.stock_consommables -= float(item.quantity_ordered)
                    stock_location_display = "Stock Consommables"
                
                if item.original_quantity and item.original_unit:
                    display_quantity = f"{item.original_quantity} × {item.original_unit.name}"
                else:
                    display_quantity = f"{item.quantity_ordered}"
                stock_reversions.append(f"{item.product.name}: -{display_quantity} du {stock_location_display}")

        if stock_reversions:
            flash(f'Stocks reversés automatiquement :', 'warning')
            for reversion in stock_reversions:
                flash(f'📦 {reversion}', 'info')

    purchase.status = PurchaseStatus.CANCELLED
    db.session.commit()
    flash(f'Bon d\'achat {purchase.reference} annulé avec succès.', 'success')
    return redirect(url_for('purchases.view_purchase', id=id))

@purchases.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_purchase(id):
    """Modification d'un bon d'achat avec support des unités"""
    Product, User, Unit = get_main_models()
    purchase = Purchase.query.get_or_404(id)

    if not current_user.is_admin and purchase.requested_by_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation de modifier ce bon d\'achat.', 'danger')
        return redirect(url_for('purchases.list_purchases'))

    if purchase.status not in [PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED, PurchaseStatus.RECEIVED]:
        flash('Ce bon d\'achat ne peut plus être modifié dans son état actuel.', 'warning')
        return redirect(url_for('purchases.view_purchase', id=id))

    form = PurchaseForm(obj=purchase)
    
    if form.validate_on_submit():
        # ### DEBUT DE LA CORRECTION ###
        # Mise à jour de la date à partir des données du formulaire.
        # Le bloc défectueux 'request.form.get('purchase_date')' a été supprimé.
        purchase.requested_date = form.requested_date.data
        # ### FIN DE LA CORRECTION ###

        old_stock_updates = []
        if purchase.status == PurchaseStatus.RECEIVED:
            for item in purchase.items:
                if item.product:
                    old_stock_updates.append({
                        'product': item.product,
                        'location': item.stock_location,
                        'quantity': float(item.quantity_ordered)
                    })
        
        purchase.supplier_name = form.supplier_name.data
        purchase.supplier_contact = form.supplier_contact.data
        purchase.supplier_phone = form.supplier_phone.data
        purchase.supplier_email = form.supplier_email.data
        purchase.supplier_address = form.supplier_address.data
        purchase.expected_delivery_date = form.expected_delivery_date.data
        purchase.urgency = PurchaseUrgency(form.urgency.data)
        purchase.payment_terms = form.payment_terms.data
        purchase.shipping_cost = form.shipping_cost.data or 0.0
        purchase.tax_amount = form.tax_amount.data or 0.0
        purchase.notes = form.notes.data
        purchase.internal_notes = form.internal_notes.data
        purchase.terms_conditions = form.terms_conditions.data

        for old_update in old_stock_updates:
            product = old_update['product']
            location = old_update['location']
            quantity = old_update['quantity']
            if location == 'ingredients_magasin':
                product.stock_ingredients_magasin -= quantity
            elif location == 'ingredients_local':
                product.stock_ingredients_local -= quantity
            elif location == 'comptoir':
                product.stock_comptoir -= quantity
            elif location == 'consommables':
                product.stock_consommables -= quantity

        PurchaseItem.query.filter_by(purchase_id=purchase.id).delete()

        items_added = 0
        product_ids = request.form.getlist('items[][product_id]')
        quantities = request.form.getlist('items[][quantity_ordered]')
        prices = request.form.getlist('items[][unit_price]')
        units = request.form.getlist('items[][unit]')
        stock_locations = request.form.getlist('items[][stock_location]') 

        for i in range(len(product_ids)):
            try:
                product_id = int(product_ids[i]) if product_ids[i] else None
                quantity = float(quantities[i]) if quantities[i] else 0
                price = float(prices[i]) if prices[i] else 0
                unit_id = int(units[i]) if units[i] else None
                stock_location = stock_locations[i] if i < len(stock_locations) else 'ingredients_magasin' 

                if product_id and quantity > 0 and price > 0:
                    final_quantity = quantity
                    final_unit_price = price
                    original_quantity = None
                    original_unit_id = None
                    original_unit_price = None
                    description_with_unit = f"{quantity} unités"
                    if unit_id:
                        try:
                            unit = Unit.query.get(unit_id)
                            if unit and unit.conversion_factor > 0:
                                final_quantity = unit.to_base_unit(quantity)
                                final_unit_price = price / float(unit.conversion_factor)
                                original_quantity = quantity
                                original_unit_id = unit.id
                                original_unit_price = price
                                description_with_unit = f"{quantity} × {unit.name}"
                        except (ValueError, TypeError):
                            pass
                    
                    purchase_item = PurchaseItem(
                        purchase_id=purchase.id,
                        product_id=product_id,
                        quantity_ordered=final_quantity,
                        unit_price=final_unit_price,
                        original_quantity=original_quantity,
                        original_unit_id=original_unit_id,
                        original_unit_price=original_unit_price,
                        stock_location=stock_location,
                        description_override=description_with_unit
                    )
                    db.session.add(purchase_item)
                    items_added += 1
            except (ValueError, IndexError, TypeError) as e:
                print(f"Erreur traitement item {i}: {e}")
                continue

        if items_added == 0:
            flash('Aucun article valide n\'a été ajouté au bon d\'achat.', 'danger')
            available_products = Product.query.filter(
                Product.product_type.in_(['ingredient', 'consommable'])
            ).all()
            available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
            return render_template('purchases/edit_purchase.html', form=form, purchase=purchase,
                                title='Modifier Bon d\'Achat', available_products=available_products,
                                available_units=available_units)
        
        if purchase.status == PurchaseStatus.RECEIVED:
            for item in purchase.items:
                if item.product:
                    if item.stock_location == 'ingredients_magasin':
                        item.product.stock_ingredients_magasin += float(item.quantity_ordered)
                    elif item.stock_location == 'ingredients_local':
                        item.product.stock_ingredients_local += float(item.quantity_ordered)
                    elif item.stock_location == 'comptoir':
                        item.product.stock_comptoir += float(item.quantity_ordered)
                    elif item.stock_location == 'consommables':
                        item.product.stock_consommables += float(item.quantity_ordered)

        purchase.calculate_totals()
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} modifié avec succès.', 'success')
        return redirect(url_for('purchases.view_purchase', id=purchase.id))

    available_products = Product.query.filter(
        Product.product_type.in_(['ingredient', 'consommable'])
    ).all()
    available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
    return render_template(
        'purchases/edit_purchase.html',
        form=form,
        purchase=purchase,
        title=f'Modifier Bon d\'Achat {purchase.reference}',
        available_products=available_products,
        available_units=available_units
    )


# ==================== ROUTES API/AJAX ====================

@purchases.route('/api/products_search')
@login_required
def api_products_search():
    """API de recherche de produits pour l'auto-complétion"""
    Product, User, Unit = get_main_models()
    search_term = request.args.get('q', '')
    if len(search_term) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        and_(
            Product.name.ilike(f'%{search_term}%'),
            Product.product_type.in_(['ingredient', 'consommable'])
        )
    ).limit(20).all()

    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'unit': product.unit,
            'cost_price': float(product.cost_price or 0),
            'stock_magasin': product.stock_ingredients_magasin,
            'stock_local': product.stock_ingredients_local
        })
    return jsonify(results)

@purchases.route('/api/pending_count')
@login_required
@admin_required
def api_pending_count():
    """API pour le nombre d'achats en attente d'approbation"""
    count = Purchase.query.filter(
        Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
    ).count()
    return jsonify({'count': count})

@purchases.route('/api/products/<int:product_id>/units')
@login_required
def api_product_units(product_id):
    """API pour récupérer les unités disponibles pour un produit"""
    Product, User, Unit = get_main_models()
    product = Product.query.get_or_404(product_id)
    units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
    
    results = []
    for unit in units:
        results.append({
            'id': unit.id,
            'name': unit.name,
            'base_unit': unit.base_unit,
            'conversion_factor': float(unit.conversion_factor),
            'unit_type': unit.unit_type
        })
    return jsonify(results)