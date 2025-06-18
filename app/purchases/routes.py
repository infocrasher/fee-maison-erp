"""
Routes pour la gestion des achats fournisseurs avec système d'unités

Module: app/purchases/routes.py

Auteur: ERP Fée Maison
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from extensions import db
from .models import Purchase, PurchaseItem, PurchaseStatus, PurchaseUrgency
from .forms import (PurchaseForm, PurchaseApprovalForm, PurchaseReceiptForm,
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
    """Liste de tous les achats avec filtres"""
    Product, User, Unit = get_main_models()
    
    form = PurchaseSearchForm()
    
    # Construction de la requête de base
    query = Purchase.query
    
    # Application des filtres si formulaire soumis
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
    
    # Statistiques pour le dashboard
    stats = {
        'total_purchases': Purchase.query.count(),
        'pending_approval': Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
        ).count(),
        'in_progress': Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.ORDERED, PurchaseStatus.PARTIALLY_RECEIVED])
        ).count(),
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
        total_amount_month=0,  # À calculer si nécessaire
        suppliers_count=len(suppliers_list),
        suppliers_list=suppliers_list,
        pagination=purchases
    )

@purchases.route('/new', methods=['GET', 'POST'])
@login_required
def new_purchase():
    """Création d'un nouveau bon d'achat avec support des unités"""
    Product, User, Unit = get_main_models()
    
    form = PurchaseForm()
    
    if form.validate_on_submit():
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
            requested_by_id=current_user.id
        )
        
        # Statut selon l'action choisie
        if 'submit_and_request' in request.form:
            purchase.status = PurchaseStatus.REQUESTED
        else:
            purchase.status = PurchaseStatus.DRAFT
        
        db.session.add(purchase)
        db.session.flush()  # Pour obtenir l'ID
        
        # ✅ NOUVELLE LOGIQUE : Ajout des lignes avec conversion d'unités
        items_added = 0
        for item_data in form.items.data:
            if (item_data.get('product_id') and
                item_data.get('quantity_ordered', 0) > 0 and
                item_data.get('unit_price', 0) > 0):
                
                # ✅ GESTION CONVERSION D'UNITÉS
                quantity_ordered = float(item_data['quantity_ordered'])
                unit_price = float(item_data['unit_price'])
                unit_id = item_data.get('unit')
                
                # Variables pour la sauvegarde
                final_quantity = quantity_ordered
                final_unit_price = unit_price
                original_quantity = None
                original_unit_id = None
                original_unit_price = None
                description_with_unit = f"{quantity_ordered} unités"
                
                # Si une unité de conditionnement est sélectionnée
                if unit_id:
                    try:
                        unit = Unit.query.get(int(unit_id))
                        if unit:
                            # Calcul quantité en unité de base
                            final_quantity = unit.to_base_unit(quantity_ordered)
                            final_unit_price = unit_price / float(unit.conversion_factor)
                            
                            # Sauvegarde des valeurs originales
                            original_quantity = quantity_ordered
                            original_unit_id = unit.id
                            original_unit_price = unit_price
                            description_with_unit = f"{quantity_ordered} × {unit.name}"
                            
                            flash(f'Conversion : {quantity_ordered} × {unit.name} = {final_quantity}{unit.base_unit}', 'info')
                    except (ValueError, TypeError):
                        # En cas d'erreur, on garde les valeurs originales
                        pass
                
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=item_data['product_id'],
                    quantity_ordered=final_quantity,      # ✅ Quantité en unité de base
                    unit_price=final_unit_price,          # ✅ Prix par unité de base
                    original_quantity=original_quantity,   # ✅ Quantité originale (ex: 2)
                    original_unit_id=original_unit_id,     # ✅ Unité originale (ex: 25kg)
                    original_unit_price=original_unit_price, # ✅ Prix original (ex: 1500 DA/sac)
                    discount_percentage=item_data.get('discount_percentage', 0.0),
                    stock_location=item_data.get('stock_location', purchase.default_stock_location),
                    description_override=description_with_unit,
                    supplier_reference=item_data.get('supplier_reference'),
                    notes=item_data.get('notes')
                )
                
                db.session.add(purchase_item)
                items_added += 1
        
        if items_added == 0:
            flash('Aucun article valide n\'a été ajouté au bon d\'achat.', 'danger')
            return render_template('purchases/new_purchase.html', form=form, title='Nouveau Bon d\'Achat')
        
        # Calcul des totaux
        purchase.calculate_totals()
        db.session.commit()
        
        action_text = "créé et demandé pour approbation" if purchase.status == PurchaseStatus.REQUESTED else "créé en brouillon"
        flash(f'Bon d\'achat {purchase.reference} {action_text} avec {items_added} article(s).', 'success')
        
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    # Variables pour le template
    available_products = Product.query.filter(
        Product.product_type.in_(['ingredient', 'consommable'])
    ).all()
    
    # ✅ AJOUT : Unités disponibles pour le template
    available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
    
    return render_template(
        'purchases/new_purchase.html', 
        form=form, 
        title='Nouveau Bon d\'Achat',
        available_products=available_products,
        available_units=available_units  # ✅ NOUVEAU
    )

@purchases.route('/<int:id>')
@login_required
def view_purchase(id):
    """Affichage détaillé d'un bon d'achat avec unités"""
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
    
    if form.validate_on_submit():
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
        
        # ✅ LOGIQUE IDENTIQUE : Mise à jour des lignes avec conversions
        PurchaseItem.query.filter_by(purchase_id=purchase.id).delete()
        
        items_added = 0
        for item_data in form.items.data:
            if (item_data.get('product_id') and
                item_data.get('quantity_ordered', 0) > 0 and
                item_data.get('unit_price', 0) > 0):
                
                # Conversion d'unités (même logique que new_purchase)
                quantity_ordered = float(item_data['quantity_ordered'])
                unit_price = float(item_data['unit_price'])
                unit_id = item_data.get('unit')
                
                final_quantity = quantity_ordered
                final_unit_price = unit_price
                original_quantity = None
                original_unit_id = None
                original_unit_price = None
                description_with_unit = f"{quantity_ordered} unités"
                
                if unit_id:
                    try:
                        unit = Unit.query.get(int(unit_id))
                        if unit:
                            final_quantity = unit.to_base_unit(quantity_ordered)
                            final_unit_price = unit_price / float(unit.conversion_factor)
                            original_quantity = quantity_ordered
                            original_unit_id = unit.id
                            original_unit_price = unit_price
                            description_with_unit = f"{quantity_ordered} × {unit.name}"
                    except (ValueError, TypeError):
                        pass
                
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=item_data['product_id'],
                    quantity_ordered=final_quantity,
                    unit_price=final_unit_price,
                    original_quantity=original_quantity,
                    original_unit_id=original_unit_id,
                    original_unit_price=original_unit_price,
                    discount_percentage=item_data.get('discount_percentage', 0.0),
                    stock_location=item_data.get('stock_location', purchase.default_stock_location),
                    description_override=description_with_unit,
                    supplier_reference=item_data.get('supplier_reference'),
                    notes=item_data.get('notes')
                )
                
                db.session.add(purchase_item)
                items_added += 1
        
        if items_added == 0:
            flash('Aucun article valide n\'a été ajouté au bon d\'achat.', 'danger')
            return render_template('purchases/edit_purchase.html', form=form, purchase=purchase, title='Modifier Bon d\'Achat')
        
        # Recalcul des totaux
        purchase.calculate_totals()
        db.session.commit()
        
        flash(f'Bon d\'achat {purchase.reference} modifié avec succès.', 'success')
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    # Variables pour le template
    available_products = Product.query.filter(
        Product.product_type.in_(['ingredient', 'consommable'])
    ).all()
    
    # ✅ AJOUT : Unités disponibles
    available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
    
    return render_template(
        'purchases/edit_purchase.html',
        form=form,
        purchase=purchase,
        title=f'Modifier Bon d\'Achat {purchase.reference}',
        available_products=available_products,
        available_units=available_units  # ✅ NOUVEAU
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

# ✅ NOUVELLE API : Unités disponibles pour un produit
@purchases.route('/api/products/<int:product_id>/units')
@login_required
def api_product_units(product_id):
    """API pour récupérer les unités disponibles pour un produit"""
    Product, User, Unit = get_main_models()
    
    product = Product.query.get_or_404(product_id)
    
    # Pour l'instant, toutes les unités sont disponibles
    # Plus tard, on filtrera selon les associations product-unit
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
