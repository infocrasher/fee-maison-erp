"""
Routes pour la gestion des achats fournisseurs
Module: app/purchases/routes.py
Auteur: ERP Fée Maison
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from extensions import db
# CORRECTION : Import local pour éviter la circularité
from .models import Purchase, PurchaseItem, PurchaseStatus, PurchaseUrgency
from .forms import (PurchaseForm, PurchaseApprovalForm, PurchaseReceiptForm, 
                    PurchaseSearchForm, QuickPurchaseForm, PurchaseReceiptItemForm)
from decorators import admin_required
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import json

# Import du blueprint depuis __init__.py
from . import bp as purchases

# Fonction helper pour récupérer les modèles principaux
def get_main_models():
    """Fonction helper pour importer Product et User sans circularité"""
    import sys
    if 'models' in sys.modules:
        models_module = sys.modules['models']
        return models_module.Product, models_module.User
    else:
        # Import direct si le module principal n'est pas encore chargé
        from models import Product, User
        return Product, User

# ==================== ROUTES PRINCIPALES CRUD ====================

@purchases.route('/')
@login_required
def list_purchases():
    """Liste de tous les achats avec filtres"""
    Product, User = get_main_models()
    
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
    
    return render_template(
        'purchases/list_purchases.html',
        title="Gestion des Achats",
        purchases=purchases,
        form=form,
        stats=stats
    )

@purchases.route('/new', methods=['GET', 'POST'])
@login_required
def new_purchase():
    """Création d'un nouveau bon d'achat"""
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
        
        # Ajout des lignes d'articles
        items_added = 0
        for item_data in form.items.data:
            if (item_data.get('product_id') and 
                item_data.get('quantity_ordered', 0) > 0 and 
                item_data.get('unit_price', 0) > 0):
                
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=item_data['product_id'],
                    quantity_ordered=item_data['quantity_ordered'],
                    unit_price=item_data['unit_price'],
                    discount_percentage=item_data.get('discount_percentage', 0.0),
                    stock_location=item_data.get('stock_location', purchase.default_stock_location),
                    description_override=item_data.get('description_override'),
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
    
    return render_template('purchases/new_purchase.html', form=form, title='Nouveau Bon d\'Achat')

@purchases.route('/<int:id>')
@login_required
def view_purchase(id):
    """Affichage détaillé d'un bon d'achat"""
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
    """Modification d'un bon d'achat"""
    purchase = Purchase.query.get_or_404(id)
    
    # Vérifications des permissions et du statut
    if not current_user.is_admin and purchase.requested_by_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation de modifier ce bon d\'achat.', 'danger')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    if purchase.status not in [PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED]:
        flash('Ce bon d\'achat ne peut plus être modifié.', 'warning')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    form = PurchaseForm(obj=purchase)
    
    # Pré-remplissage des articles existants
    if request.method == 'GET':
        form.items.entries = []
        for item in purchase.items:
            item_form = form.items.append_entry()
            item_form.product_id.data = item.product_id
            item_form.product.data = item.product
            item_form.quantity_ordered.data = float(item.quantity_ordered)
            item_form.unit_price.data = float(item.unit_price)
            item_form.discount_percentage.data = float(item.discount_percentage)
            item_form.stock_location.data = item.stock_location
            item_form.description_override.data = item.description_override
            item_form.supplier_reference.data = item.supplier_reference
            item_form.notes.data = item.notes
    
    if form.validate_on_submit():
        # Mise à jour des informations générales
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
        purchase.updated_at = datetime.utcnow()
        
        # Suppression des anciens articles
        for item in purchase.items:
            db.session.delete(item)
        db.session.flush()
        
        # Ajout des nouveaux articles
        items_added = 0
        for item_data in form.items.data:
            if (item_data.get('product_id') and 
                item_data.get('quantity_ordered', 0) > 0 and 
                item_data.get('unit_price', 0) > 0):
                
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=item_data['product_id'],
                    quantity_ordered=item_data['quantity_ordered'],
                    unit_price=item_data['unit_price'],
                    discount_percentage=item_data.get('discount_percentage', 0.0),
                    stock_location=item_data.get('stock_location', purchase.default_stock_location),
                    description_override=item_data.get('description_override'),
                    supplier_reference=item_data.get('supplier_reference'),
                    notes=item_data.get('notes')
                )
                db.session.add(purchase_item)
                items_added += 1
        
        # Changement de statut si demandé
        if 'submit_and_request' in request.form:
            purchase.status = PurchaseStatus.REQUESTED
        
        # Recalcul des totaux
        purchase.calculate_totals()
        
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} modifié avec succès.', 'success')
        
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    return render_template(
        'purchases/edit_purchase.html',
        form=form,
        purchase=purchase,
        title=f'Modifier {purchase.reference}'
    )

# ==================== ROUTES DE WORKFLOW ====================

@purchases.route('/<int:id>/approve', methods=['GET', 'POST'])
@login_required
@admin_required
def approve_purchase(id):
    """Approbation d'un bon d'achat"""
    purchase = Purchase.query.get_or_404(id)
    
    if not purchase.can_be_approved:
        flash('Ce bon d\'achat ne peut pas être approuvé dans son état actuel.', 'warning')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    form = PurchaseApprovalForm()
    
    # Pré-remplissage avec les valeurs actuelles
    if request.method == 'GET':
        form.shipping_cost.data = float(purchase.shipping_cost or 0)
        form.tax_amount.data = float(purchase.tax_amount or 0)
        form.expected_delivery_date.data = purchase.expected_delivery_date
    
    if form.validate_on_submit():
        if 'approve' in request.form:
            # Mise à jour des valeurs modifiables
            purchase.shipping_cost = form.shipping_cost.data or 0.0
            purchase.tax_amount = form.tax_amount.data or 0.0
            purchase.expected_delivery_date = form.expected_delivery_date.data
            
            # Ajout des notes d'approbation aux notes internes
            if form.approval_notes.data:
                approval_note = f"\n--- Approbation {datetime.now().strftime('%d/%m/%Y %H:%M')} ---\n{form.approval_notes.data}"
                purchase.internal_notes = (purchase.internal_notes or "") + approval_note
            
            # Approbation
            if purchase.approve(current_user.id):
                purchase.calculate_totals()  # Recalcul avec nouveaux frais
                db.session.commit()
                flash(f'Bon d\'achat {purchase.reference} approuvé avec succès.', 'success')
            else:
                flash('Erreur lors de l\'approbation.', 'danger')
        
        elif 'reject' in request.form:
            # Rejet (remise en brouillon)
            purchase.status = PurchaseStatus.DRAFT
            rejection_note = f"\n--- Rejet {datetime.now().strftime('%d/%m/%Y %H:%M')} ---\n{form.approval_notes.data or 'Aucune raison spécifiée'}"
            purchase.internal_notes = (purchase.internal_notes or "") + rejection_note
            db.session.commit()
            flash(f'Bon d\'achat {purchase.reference} rejeté et remis en brouillon.', 'warning')
        
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    return render_template(
        'purchases/approve_purchase.html',
        form=form,
        purchase=purchase,
        title=f'Approbation {purchase.reference}'
    )

@purchases.route('/<int:id>/mark_ordered', methods=['POST'])
@login_required
@admin_required
def mark_ordered(id):
    """Marquer comme commandé chez le fournisseur"""
    purchase = Purchase.query.get_or_404(id)
    
    if purchase.mark_as_ordered():
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} marqué comme commandé.', 'success')
    else:
        flash('Impossible de marquer ce bon d\'achat comme commandé.', 'danger')
    
    return redirect(url_for('purchases.view_purchase', id=id))

@purchases.route('/<int:id>/receive', methods=['GET', 'POST'])
@login_required
def receive_purchase(id):
    """Réception de marchandises"""
    purchase = Purchase.query.get_or_404(id)
    
    if not purchase.can_receive_items:
        flash('Ce bon d\'achat ne peut pas recevoir de marchandises dans son état actuel.', 'warning')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    # Traitement des réceptions par item
    if request.method == 'POST':
        receipt_notes = request.form.get('receipt_notes', '')
        items_received = 0
        errors = []
        
        for item in purchase.items:
            quantity_field = f'quantity_{item.id}'
            location_field = f'location_{item.id}'
            
            if quantity_field in request.form:
                try:
                    quantity_to_receive = float(request.form[quantity_field])
                    stock_location = request.form.get(location_field, item.stock_location)
                    
                    if quantity_to_receive > 0:
                        success, message = item.receive_quantity(
                            quantity_to_receive, 
                            current_user.id, 
                            stock_location
                        )
                        
                        if success:
                            items_received += 1
                        else:
                            errors.append(f"{item.display_name}: {message}")
                
                except (ValueError, TypeError):
                    errors.append(f"{item.display_name}: Quantité invalide")
        
        if items_received > 0:
            # Ajout des notes de réception
            if receipt_notes:
                reception_note = f"\n--- Réception {datetime.now().strftime('%d/%m/%Y %H:%M')} ---\n{receipt_notes}"
                purchase.internal_notes = (purchase.internal_notes or "") + reception_note
            
            # Mise à jour du statut selon la réception
            purchase.check_completion_status()
            
            # Marquage du réceptionnaire si première réception
            if not purchase.received_by_id:
                purchase.received_by_id = current_user.id
            
            db.session.commit()
            flash(f'Réception effectuée pour {items_received} article(s).', 'success')
            
            if errors:
                for error in errors:
                    flash(error, 'warning')
        else:
            flash('Aucun article n\'a été réceptionné.', 'warning')
        
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    return render_template(
        'purchases/receive_purchase.html',
        purchase=purchase,
        title=f'Réception {purchase.reference}'
    )

@purchases.route('/<int:id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_purchase(id):
    """Annulation d'un bon d'achat"""
    purchase = Purchase.query.get_or_404(id)
    
    if purchase.cancel():
        cancellation_note = f"\n--- Annulation {datetime.now().strftime('%d/%m/%Y %H:%M')} par {current_user.username} ---"
        purchase.internal_notes = (purchase.internal_notes or "") + cancellation_note
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} annulé.', 'success')
    else:
        flash('Impossible d\'annuler ce bon d\'achat.', 'danger')
    
    return redirect(url_for('purchases.view_purchase', id=id))

# ==================== ROUTES UTILITAIRES ====================

@purchases.route('/quick_purchase', methods=['GET', 'POST'])
@login_required
def quick_purchase():
    """Création d'un achat rapide pour un produit"""
    form = QuickPurchaseForm()
    
    if form.validate_on_submit():
        # Création du bon d'achat
        purchase = Purchase(
            supplier_name=form.supplier_name.data,
            supplier_phone=form.supplier_phone.data,
            urgency=PurchaseUrgency(form.urgency.data),
            default_stock_location=form.stock_location.data,
            notes=form.notes.data,
            requested_by_id=current_user.id,
            status=PurchaseStatus.REQUESTED  # Demande immédiate d'approbation
        )
        
        db.session.add(purchase)
        db.session.flush()
        
        # Création de l'article
        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=form.product.data.id,
            quantity_ordered=form.quantity.data,
            unit_price=form.unit_price.data,
            stock_location=form.stock_location.data
        )
        
        db.session.add(purchase_item)
        purchase.calculate_totals()
        db.session.commit()
        
        flash(f'Achat rapide {purchase.reference} créé et soumis pour approbation.', 'success')
        return redirect(url_for('purchases.view_purchase', id=purchase.id))
    
    return render_template('purchases/quick_purchase.html', form=form, title='Achat Rapide')

@purchases.route('/pending_approvals')
@login_required
@admin_required
def pending_approvals():
    """Liste des achats en attente d'approbation"""
    purchases = Purchase.query.filter(
        Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
    ).order_by(desc(Purchase.requested_date)).all()
    
    return render_template(
        'purchases/pending_approvals.html',
        title="Achats en Attente d'Approbation",
        purchases=purchases
    )

@purchases.route('/overdue')
@login_required
def overdue_purchases():
    """Liste des achats en retard de livraison"""
    from .models import get_overdue_purchases
    overdue = get_overdue_purchases()
    
    return render_template(
        'purchases/overdue_purchases.html',
        title="Achats en Retard",
        purchases=overdue
    )

# ==================== ROUTES API/AJAX ====================

@purchases.route('/api/products_search')
@login_required
def api_products_search():
    """API de recherche de produits pour l'auto-complétion"""
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

@purchases.route('/api/purchase/<int:id>/status')
@login_required
def api_purchase_status(id):
    """API pour récupérer le statut d'un achat"""
    purchase = Purchase.query.get_or_404(id)
    
    return jsonify({
        'id': purchase.id,
        'reference': purchase.reference,
        'status': purchase.status.value,
        'status_display': purchase.status_display,
        'completion_percentage': purchase.completion_percentage,
        'total_amount': float(purchase.total_amount),
        'items_count': purchase.total_items_count,
        'can_be_approved': purchase.can_be_approved,
        'can_receive_items': purchase.can_receive_items
    })

@purchases.route('/api/supplier_history/<supplier_name>')
@login_required
def api_supplier_history(supplier_name):
    """API pour l'historique d'un fournisseur"""
    from .models import get_purchases_by_supplier
    
    purchases = get_purchases_by_supplier(supplier_name)[:10]  # 10 derniers achats
    
    history = []
    for purchase in purchases:
        history.append({
            'reference': purchase.reference,
            'date': purchase.requested_date.strftime('%d/%m/%Y'),
            'amount': float(purchase.total_amount),
            'status': purchase.status_display,
            'items_count': purchase.total_items_count
        })
    
    return jsonify(history)

# ==================== ROUTES DE REPORTING ====================

@purchases.route('/reports/monthly/<int:year>/<int:month>')
@login_required
@admin_required
def monthly_report(year, month):
    """Rapport mensuel des achats"""
    from .models import get_monthly_purchase_stats
    
    stats = get_monthly_purchase_stats(year, month)
    
    # Récupération des achats du mois
    purchases = Purchase.query.filter(
        and_(
            func.extract('year', Purchase.requested_date) == year,
            func.extract('month', Purchase.requested_date) == month,
            Purchase.status != PurchaseStatus.CANCELLED
        )
    ).order_by(desc(Purchase.requested_date)).all()
    
    return render_template(
        'purchases/monthly_report.html',
        title=f"Rapport Achats {month:02d}/{year}",
        year=year,
        month=month,
        stats=stats,
        purchases=purchases
    )

@purchases.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal des achats"""
    today = datetime.now()
    last_30_days = today - timedelta(days=30)
    
    # Statistiques générales
    stats = {
        'total_purchases': Purchase.query.count(),
        'pending_approval': Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
        ).count(),
        'in_progress': Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.ORDERED, PurchaseStatus.PARTIALLY_RECEIVED])
        ).count(),
        'completed_this_month': Purchase.query.filter(
            and_(
                Purchase.status.in_([PurchaseStatus.RECEIVED, PurchaseStatus.INVOICED]),
                Purchase.received_date >= today.replace(day=1)
            )
        ).count(),
        'total_value_30_days': db.session.query(func.sum(Purchase.total_amount)).filter(
            and_(
                Purchase.requested_date >= last_30_days,
                Purchase.status != PurchaseStatus.CANCELLED
            )
        ).scalar() or 0
    }
    
    # Achats récents
    recent_purchases = Purchase.query.order_by(desc(Purchase.requested_date)).limit(10).all()
    
    # Achats en retard
    from .models import get_overdue_purchases
    overdue = get_overdue_purchases()
    
    # Achats urgents
    urgent_purchases = Purchase.query.filter(
        and_(
            Purchase.urgency == PurchaseUrgency.URGENT,
            Purchase.status.in_([PurchaseStatus.REQUESTED, PurchaseStatus.APPROVED, PurchaseStatus.ORDERED])
        )
    ).all()
    
    return render_template(
        'purchases/dashboard.html',
        title="Dashboard Achats",
        stats=stats,
        recent_purchases=recent_purchases,
        overdue_purchases=overdue,
        urgent_purchases=urgent_purchases
    )
