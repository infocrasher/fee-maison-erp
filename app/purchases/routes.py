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
    
    purchases = query.order_by(desc(Purchase.requested_date)).paginate(
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
        unpaid_purchases=stats['unpaid_purchases'],    # ✅ NOUVEAU
        paid_purchases=stats['paid_purchases'],        # ✅ NOUVEAU
        total_amount_month=0,
        suppliers_count=len(suppliers_list),
        suppliers_list=suppliers_list,
        pagination=purchases,
        current_payment_filter=payment_filter         # ✅ NOUVEAU
    )

@purchases.route('/new', methods=['GET', 'POST'])
@login_required
def new_purchase():
    """Création d'un nouveau bon d'achat avec traitement manuel des items"""
    Product, User, Unit = get_main_models()
    
    form = PurchaseForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        # Création du bon d'achat principal
        purchase = Purchase(
            supplier_name=form.supplier_name.data,
            supplier_contact=form.supplier_contact.data,
            supplier_phone=form.supplier_phone.data,
            supplier_email=form.supplier_email.data,
            supplier_address=form.supplier_address.data,
            expected_delivery_date=form.expected_delivery_date.data,
            urgency=PurchaseUrgency(form.urgency.data),
            default_stock_location=form.default_stock_location.data,
            payment_terms=form.payment_terms.data,
            shipping_cost=form.shipping_cost.data or 0.0,
            tax_amount=form.tax_amount.data or 0.0,
            notes=form.notes.data,
            internal_notes=form.internal_notes.data,
            terms_conditions=form.terms_conditions.data,
            requested_by_id=current_user.id,
            is_paid=False  # ✅ NOUVEAU : Non payé par défaut
        )
        
        # Statut selon l'action choisie
        purchase.status = PurchaseStatus.RECEIVED
        
        db.session.add(purchase)
        db.session.flush()  # Pour obtenir l'ID
        
        # Traitement manuel des items depuis request.form
        items_added = 0
        
        # Récupérer tous les champs items de request.form
        product_ids = request.form.getlist('items[][product_id]')
        quantities = request.form.getlist('items[][quantity_ordered]')
        prices = request.form.getlist('items[][unit_price]')
        units = request.form.getlist('items[][unit]')
        
        # Traiter chaque ligne d'item
        for i in range(len(product_ids)):
            try:
                product_id = int(product_ids[i]) if product_ids[i] else None
                quantity = float(quantities[i]) if quantities[i] else 0
                price = float(prices[i]) if prices[i] else 0
                unit_id = int(units[i]) if units[i] else None
                
                if product_id and quantity > 0 and price > 0:
                    # Gestion conversion d'unités
                    final_quantity = quantity
                    final_unit_price = price
                    original_quantity = None
                    original_unit_id = None
                    original_unit_price = None
                    description_with_unit = f"{quantity} unités"
                    
                    # Si une unité de conditionnement est sélectionnée
                    if unit_id:
                        try:
                            unit = Unit.query.get(unit_id)
                            if unit:
                                # Calcul quantité en unité de base
                                final_quantity = unit.to_base_unit(quantity)
                                final_unit_price = price / float(unit.conversion_factor)
                                
                                # Sauvegarde des valeurs originales
                                original_quantity = quantity
                                original_unit_id = unit.id
                                original_unit_price = price
                                description_with_unit = f"{quantity} × {unit.name}"
                                
                                flash(f'Conversion : {quantity} × {unit.name} = {final_quantity}{unit.base_unit}', 'info')
                        except (ValueError, TypeError):
                            # En cas d'erreur, on garde les valeurs originales
                            pass
                    
                    purchase_item = PurchaseItem(
                        purchase_id=purchase.id,
                        product_id=product_id,
                        quantity_ordered=final_quantity,
                        unit_price=final_unit_price,
                        original_quantity=original_quantity,
                        original_unit_id=original_unit_id,
                        original_unit_price=original_unit_price,
                        stock_location=purchase.default_stock_location,
                        description_override=description_with_unit
                    )
                    
                    db.session.add(purchase_item)
                    items_added += 1
                    
            except (ValueError, IndexError, TypeError) as e:
                print(f"Erreur traitement item {i}: {e}")
                continue
        
        if items_added == 0:
            flash('Aucun article valide n\'a été ajouté au bon d\'achat.', 'danger')
            # Variables pour le template
            available_products = Product.query.filter(
                Product.product_type.in_(['ingredient', 'consommable'])
            ).all()
            available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
            
            return render_template('purchases/new_purchase.html', form=form, title='Nouveau Bon d\'Achat',
                                 available_products=available_products, available_units=available_units)
        
        # Calcul des totaux
        purchase.calculate_totals()
        db.session.commit()
        
        action_text = "créé et demandé pour approbation" if purchase.status == PurchaseStatus.REQUESTED else "créé en brouillon"
        flash(f'Bon d\'achat {purchase.reference} {action_text} avec {items_added} article(s).', 'success')
        
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    # Debug des erreurs de validation
    elif request.method == 'POST':
        flash('Erreur de validation du formulaire. Vérifiez les champs.', 'danger')
        if form.errors:
            for field_name, errors in form.errors.items():
                for error in errors:
                    flash(f"Erreur {field_name}: {error}", 'warning')
    
    # Variables pour le template
    available_products = Product.query.filter(
        Product.product_type.in_(['ingredient', 'consommable'])
    ).all()
    available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
    
    return render_template(
        'purchases/new_purchase.html', 
        form=form, 
        title='Nouveau Bon d\'Achat',
        available_products=available_products,
        available_units=available_units
    )

@purchases.route('/<int:id>')
@login_required
def view_purchase(id):
    """Affichage détaillé d'un bon d'achat avec unités et paiement"""
    purchase = Purchase.query.get_or_404(id)
    
    # Vérification des permissions
    if not current_user.is_admin and purchase.requested_by_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation de voir ce bon d\'achat.', 'danger')
        return redirect(url_for('purchases.list_purchases'))
    
    return render_template(
        'purchases/view_purchase.html',
        title=f"Bon d'Achat {purchase.reference}",
        purchase=purchase
    )

# ✅ NOUVELLES ROUTES : Gestion des paiements
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

@purchases.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_purchase(id):
    """Modification d'un bon d'achat avec support des unités"""
    Product, User, Unit = get_main_models()
    
    purchase = Purchase.query.get_or_404(id)
    
    # Vérification des permissions
    if not current_user.is_admin and purchase.requested_by_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation de modifier ce bon d\'achat.', 'danger')
        return redirect(url_for('purchases.list_purchases'))
    
    # Vérification du statut
    if purchase.status not in [PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED]:
        flash('Ce bon d\'achat ne peut plus être modifié dans son état actuel.', 'warning')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    form = PurchaseForm(obj=purchase)
    
    if request.method == 'POST' and form.validate_on_submit():
        # Mise à jour des informations principales
        purchase.supplier_name = form.supplier_name.data
        purchase.supplier_contact = form.supplier_contact.data
        purchase.supplier_phone = form.supplier_phone.data
        purchase.supplier_email = form.supplier_email.data
        purchase.supplier_address = form.supplier_address.data
        purchase.expected_delivery_date = form.expected_delivery_date.data
        purchase.urgency = PurchaseUrgency(form.urgency.data)
        purchase.default_stock_location = form.default_stock_location.data
        purchase.payment_terms = form.payment_terms.data
        purchase.shipping_cost = form.shipping_cost.data or 0.0
        purchase.tax_amount = form.tax_amount.data or 0.0
        purchase.notes = form.notes.data
        purchase.internal_notes = form.internal_notes.data
        purchase.terms_conditions = form.terms_conditions.data
        
        # Statut selon l'action choisie
        if 'submit_and_request' in request.form:
            purchase.status = PurchaseStatus.REQUESTED
        
        # Suppression des anciennes lignes
        PurchaseItem.query.filter_by(purchase_id=purchase.id).delete()
        
        # Traitement manuel des nouvelles lignes (même logique que new_purchase)
        items_added = 0
        product_ids = request.form.getlist('items[][product_id]')
        quantities = request.form.getlist('items[][quantity_ordered]')
        prices = request.form.getlist('items[][unit_price]')
        units = request.form.getlist('items[][unit]')
        
        for i in range(len(product_ids)):
            try:
                product_id = int(product_ids[i]) if product_ids[i] else None
                quantity = float(quantities[i]) if quantities[i] else 0
                price = float(prices[i]) if prices[i] else 0
                unit_id = int(units[i]) if units[i] else None
                
                if product_id and quantity > 0 and price > 0:
                    # Conversion d'unités (même logique que new_purchase)
                    final_quantity = quantity
                    final_unit_price = price
                    original_quantity = None
                    original_unit_id = None
                    original_unit_price = None
                    description_with_unit = f"{quantity} unités"
                    
                    if unit_id:
                        try:
                            unit = Unit.query.get(unit_id)
                            if unit:
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
                        stock_location=purchase.default_stock_location,
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
        
        # Recalcul des totaux
        purchase.calculate_totals()
        db.session.commit()
        
        flash(f'Bon d\'achat {purchase.reference} modifié avec succès.', 'success')
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    # Variables pour le template
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
    
    # Pour l'instant, toutes les unités sont disponibles
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
