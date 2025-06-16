"""
Routes pour la gestion des 4 stocks et transferts
Module: app/stock/routes.py
Auteur: ERP Fée Maison
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Product, User
from .models import StockMovement, StockTransfer, StockTransferLine, StockLocationType, StockMovementType, TransferStatus
from .forms import StockAdjustmentForm, QuickStockEntryForm, StockTransferForm, MultiLocationAdjustmentForm
from decorators import admin_required
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

# Import du blueprint depuis __init__.py
from . import bp as stock

# ==================== ROUTES EXISTANTES CONSERVÉES ====================

@stock.route('/overview')
@login_required
@admin_required
def overview():
    """Vue d'ensemble globale des 4 stocks"""
    low_stock_threshold = current_app.config.get('LOW_STOCK_THRESHOLD', 5)
    
    # Récupération des produits avec stocks faibles par localisation
    products = Product.query.all()
    
    # Analyse par localisation
    comptoir_low = [p for p in products if p.is_low_stock_by_location('comptoir')]
    local_low = [p for p in products if p.is_low_stock_by_location('ingredients_local')]
    magasin_low = [p for p in products if p.is_low_stock_by_location('ingredients_magasin')]
    consommables_low = [p for p in products if p.is_low_stock_by_location('consommables')]
    
    # Calcul des valeurs totales par stock
    total_value_comptoir = sum(p.stock_comptoir * float(p.cost_price or 0) for p in products)
    total_value_local = sum(p.stock_ingredients_local * float(p.cost_price or 0) for p in products)
    total_value_magasin = sum(p.stock_ingredients_magasin * float(p.cost_price or 0) for p in products)
    total_value_consommables = sum(p.stock_consommables * float(p.cost_price or 0) for p in products)
    
    # Transferts en attente
    pending_transfers = StockTransfer.query.filter(
        StockTransfer.status.in_([TransferStatus.REQUESTED, TransferStatus.APPROVED])
    ).count()
    
    return render_template(
        'stock/stock_overview.html',
        title="Vue d'ensemble des 4 Stocks",
        comptoir_low=comptoir_low,
        local_low=local_low,
        magasin_low=magasin_low,
        consommables_low=consommables_low,
        total_value_comptoir=total_value_comptoir,
        total_value_local=total_value_local,
        total_value_magasin=total_value_magasin,
        total_value_consommables=total_value_consommables,
        pending_transfers=pending_transfers
    )

@stock.route('/quick_entry', methods=['GET', 'POST'])
@login_required
@admin_required
def quick_entry():
    """Réception rapide avec sélection de localisation"""
    form = QuickStockEntryForm()
    if form.validate_on_submit():
        product_obj = form.product.data
        quantity_received = form.quantity_received.data
        location_type = form.location_type.data
        
        # Mise à jour du stock selon la localisation
        if product_obj.update_stock_location(location_type, quantity_received):
            db.session.commit()
            
            # Création du mouvement de traçabilité
            from .models import update_stock_quantity
            update_stock_quantity(
                product_obj.id,
                getattr(StockLocationType, location_type.upper()),
                quantity_received,
                current_user.id,
                reason=f"Réception rapide - {form.reason.data or 'Arrivage marchandise'}"
            )
            
            flash(f'Stock {product_obj.get_location_display_name(location_type)} pour "{product_obj.name}" mis à jour : +{quantity_received}.', 'success')
        else:
            flash('Erreur lors de la mise à jour du stock.', 'danger')
            
        return redirect(url_for('stock.quick_entry'))
    
    return render_template('stock/quick_stock_entry.html', form=form, title='Réception Rapide Multi-Stocks')

@stock.route('/adjustment', methods=['GET', 'POST'])
@login_required
@admin_required
def adjustment():
    """Ajustement de stock avec sélection de localisation"""
    form = MultiLocationAdjustmentForm()
    if form.validate_on_submit():
        product_obj = form.product.data
        location_type = form.location_type.data
        quantity_change = form.quantity.data
        reason = form.reason.data
        
        # Récupération du stock actuel
        current_stock = product_obj.get_stock_by_location_type(location_type)
        new_stock = current_stock + quantity_change
        
        if new_stock < 0:
            flash(f'Le stock {product_obj.get_location_display_name(location_type)} de "{product_obj.name}" ne peut pas devenir négatif.', 'danger')
        else:
            # Mise à jour du stock
            if product_obj.update_stock_location(location_type, quantity_change):
                db.session.commit()
                
                # Création du mouvement de traçabilité
                from .models import update_stock_quantity
                update_stock_quantity(
                    product_obj.id,
                    getattr(StockLocationType, location_type.upper()),
                    quantity_change,
                    current_user.id,
                    reason=reason or "Ajustement manuel"
                )
                
                flash(f'Stock {product_obj.get_location_display_name(location_type)} de "{product_obj.name}" ajusté : {current_stock:+.2f} → {new_stock:.2f}.', 'success')
            else:
                flash('Erreur lors de l\'ajustement du stock.', 'danger')
                
        return redirect(url_for('stock.adjustment'))
    
    return render_template('stock/stock_adjustment_form.html', form=form, title='Ajustement Multi-Stocks')

# ==================== NOUVELLES ROUTES POUR LES 4 DASHBOARDS ====================

@stock.route('/dashboard/magasin')
@login_required
def dashboard_magasin():
    """Dashboard Stock Magasin - Interface Amel"""
    # Produits avec stock magasin
    products_magasin = Product.query.filter(Product.stock_ingredients_magasin > 0).all()
    
    # Alertes stock faible magasin
    low_stock_magasin = [p for p in Product.query.all() if p.is_low_stock_by_location('ingredients_magasin')]
    
    # Valeur totale stock magasin
    total_value = sum(p.stock_ingredients_magasin * float(p.cost_price or 0) for p in products_magasin)
    
    # Transferts sortants depuis magasin
    outgoing_transfers = StockTransfer.query.filter(
        StockTransfer.source_location == StockLocationType.INGREDIENTS_MAGASIN
    ).order_by(StockTransfer.requested_date.desc()).limit(10).all()
    
    # Demandes de transfert vers magasin
    incoming_requests = StockTransfer.query.filter(
        and_(
            StockTransfer.destination_location == StockLocationType.INGREDIENTS_MAGASIN,
            StockTransfer.status == TransferStatus.REQUESTED
        )
    ).order_by(StockTransfer.requested_date.desc()).all()
    
    return render_template(
        'stock/dashboard_magasin.html',
        title="Dashboard Stock Magasin",
        products_magasin=products_magasin,
        low_stock_magasin=low_stock_magasin,
        total_value=total_value,
        outgoing_transfers=outgoing_transfers,
        incoming_requests=incoming_requests,
        total_ingredients=len(products_magasin),
        low_stock_count=len(low_stock_magasin),
        pending_transfers=len(incoming_requests)
    )

@stock.route('/dashboard/local')
@login_required
def dashboard_local():
    """Dashboard Stock Local - Interface Rayan"""
    # Produits avec stock local
    products_local = Product.query.filter(Product.stock_ingredients_local > 0).all()
    
    # Alertes stock faible local
    low_stock_local = [p for p in Product.query.all() if p.is_low_stock_by_location('ingredients_local')]
    
    # Valeur totale stock local
    total_value = sum(p.stock_ingredients_local * float(p.cost_price or 0) for p in products_local)
    
    # Transferts récents vers local
    recent_transfers = StockTransfer.query.filter(
        StockTransfer.destination_location == StockLocationType.INGREDIENTS_LOCAL
    ).order_by(StockTransfer.completed_date.desc()).limit(5).all()
    
    # Demandes de transfert en attente
    pending_requests = StockTransfer.query.filter(
        and_(
            StockTransfer.source_location == StockLocationType.INGREDIENTS_LOCAL,
            StockTransfer.status.in_([TransferStatus.REQUESTED, TransferStatus.APPROVED])
        )
    ).all()
    
    return render_template(
        'stock/dashboard_local.html',
        title="Dashboard Stock Local Production",
        products_local=products_local,
        low_stock_local=low_stock_local,
        total_value=total_value,
        recent_transfers=recent_transfers,
        pending_requests=pending_requests,
        total_ingredients=len(products_local),
        low_stock_count=len(low_stock_local)
    )

@stock.route('/dashboard/comptoir')
@login_required
def dashboard_comptoir():
    """Dashboard Stock Comptoir - Interface Yasmine"""
    # Produits avec stock comptoir
    products_comptoir = Product.query.filter(Product.stock_comptoir > 0).all()
    
    # Alertes stock faible comptoir
    low_stock_comptoir = [p for p in Product.query.all() if p.is_low_stock_by_location('comptoir')]
    
    # Valeur totale stock comptoir
    total_value = sum(p.stock_comptoir * float(p.cost_price or 0) for p in products_comptoir)
    
    # Mouvements récents comptoir
    recent_movements = StockMovement.query.filter(
        StockMovement.stock_location == StockLocationType.COMPTOIR
    ).order_by(StockMovement.created_at.desc()).limit(10).all()
    
    return render_template(
        'stock/dashboard_comptoir.html',
        title="Dashboard Stock Comptoir",
        products_comptoir=products_comptoir,
        low_stock_comptoir=low_stock_comptoir,
        total_value=total_value,
        recent_movements=recent_movements,
        total_products=len(products_comptoir),
        low_stock_count=len(low_stock_comptoir)
    )

@stock.route('/dashboard/consommables')
@login_required
def dashboard_consommables():
    """Dashboard Stock Consommables - Interface Amel"""
    # Produits consommables
    products_consommables = Product.query.filter(
        and_(
            Product.stock_consommables > 0,
            Product.product_type == 'consommable'
        )
    ).all()
    
    # Alertes stock faible consommables
    low_stock_consommables = [p for p in Product.query.all() if p.is_low_stock_by_location('consommables')]
    
    # Valeur totale stock consommables
    total_value = sum(p.stock_consommables * float(p.cost_price or 0) for p in products_consommables)
    
    # Ajustements récents
    recent_adjustments = StockMovement.query.filter(
        and_(
            StockMovement.stock_location == StockLocationType.CONSOMMABLES,
            StockMovement.movement_type.in_([StockMovementType.AJUSTEMENT_POSITIF, StockMovementType.AJUSTEMENT_NEGATIF])
        )
    ).order_by(StockMovement.created_at.desc()).limit(5).all()
    
    return render_template(
        'stock/dashboard_consommables.html',
        title="Dashboard Stock Consommables",
        products_consommables=products_consommables,
        low_stock_consommables=low_stock_consommables,
        total_value=total_value,
        recent_adjustments=recent_adjustments,
        total_consommables=len(products_consommables),
        low_stock_count=len(low_stock_consommables)
    )

# ==================== ROUTES GESTION DES TRANSFERTS ====================

@stock.route('/transfers')
@login_required
def transfers_list():
    """Liste des transferts entre stocks"""
    transfers = StockTransfer.query.order_by(StockTransfer.requested_date.desc()).all()
    
    return render_template(
        'stock/transfers.html',
        title="Gestion des Transferts",
        transfers=transfers
    )

@stock.route('/transfers/create', methods=['GET', 'POST'])
@login_required
def create_transfer():
    """Création d'un nouveau transfert"""
    form = StockTransferForm()
    
    if form.validate_on_submit():
        # Création du transfert principal
        transfer = StockTransfer(
            source_location=getattr(StockLocationType, form.source_location.data.upper()),
            destination_location=getattr(StockLocationType, form.destination_location.data.upper()),
            requested_by_id=current_user.id,
            reason=form.reason.data,
            notes=form.notes.data,
            priority=form.priority.data
        )
        
        db.session.add(transfer)
        db.session.flush()  # Pour obtenir l'ID du transfert
        
        # Ajout des lignes de transfert
        for line_data in form.transfer_lines.data:
            if line_data['product_id'] and line_data['quantity_requested'] > 0:
                transfer_line = StockTransferLine(
                    transfer_id=transfer.id,
                    product_id=line_data['product_id'],
                    quantity_requested=line_data['quantity_requested'],
                    unit_cost=Product.query.get(line_data['product_id']).cost_price or 0.0,
                    notes=line_data.get('notes', '')
                )
                db.session.add(transfer_line)
        
        db.session.commit()
        flash(f'Transfert {transfer.reference} créé avec succès.', 'success')
        return redirect(url_for('stock.transfers_list'))
    
    return render_template(
        'stock/create_transfer.html',
        title="Créer un Transfert",
        form=form
    )

@stock.route('/transfers/<int:transfer_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_transfer(transfer_id):
    """Approbation d'un transfert"""
    transfer = StockTransfer.query.get_or_404(transfer_id)
    
    if transfer.approve(current_user.id):
        db.session.commit()
        flash(f'Transfert {transfer.reference} approuvé.', 'success')
    else:
        flash('Impossible d\'approuver ce transfert.', 'danger')
    
    return redirect(url_for('stock.transfers_list'))

@stock.route('/transfers/<int:transfer_id>/complete', methods=['POST'])
@login_required
def complete_transfer(transfer_id):
    """Finalisation d'un transfert avec mise à jour des stocks"""
    transfer = StockTransfer.query.get_or_404(transfer_id)
    
    if not transfer.can_be_completed:
        flash('Ce transfert ne peut pas être finalisé.', 'danger')
        return redirect(url_for('stock.transfers_list'))
    
    try:
        # Traitement de chaque ligne de transfert
        for line in transfer.transfer_lines:
            product = line.product
            quantity = line.quantity_requested
            
            # Vérification du stock source
            source_stock = product.get_stock_by_location_type(transfer.source_location.value)
            if source_stock < quantity:
                flash(f'Stock insuffisant pour {product.name} (disponible: {source_stock}, demandé: {quantity}).', 'danger')
                return redirect(url_for('stock.transfers_list'))
            
            # Décrémentation stock source
            product.update_stock_location(transfer.source_location.value, -quantity)
            
            # Incrémentation stock destination
            product.update_stock_location(transfer.destination_location.value, quantity)
            
            # Création des mouvements de traçabilité
            # Mouvement sortie
            movement_out = StockMovement(
                product_id=product.id,
                stock_location=transfer.source_location,
                movement_type=StockMovementType.TRANSFERT_SORTIE,
                quantity=-quantity,
                unit_cost=line.unit_cost,
                user_id=current_user.id,
                transfer_id=transfer.id,
                reason=f"Transfert {transfer.reference} - Sortie"
            )
            db.session.add(movement_out)
            
            # Mouvement entrée
            movement_in = StockMovement(
                product_id=product.id,
                stock_location=transfer.destination_location,
                movement_type=StockMovementType.TRANSFERT_ENTREE,
                quantity=quantity,
                unit_cost=line.unit_cost,
                user_id=current_user.id,
                transfer_id=transfer.id,
                reason=f"Transfert {transfer.reference} - Entrée"
            )
            db.session.add(movement_in)
            
            # Mise à jour de la ligne de transfert
            line.quantity_transferred = quantity
        
        # Finalisation du transfert
        transfer.complete(current_user.id)
        db.session.commit()
        
        flash(f'Transfert {transfer.reference} finalisé avec succès.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la finalisation du transfert: {str(e)}', 'danger')
    
    return redirect(url_for('stock.transfers_list'))

# ==================== ROUTES API/AJAX ====================

@stock.route('/api/stock_levels/<int:product_id>')
@login_required
def api_stock_levels(product_id):
    """API pour récupérer les niveaux de stock d'un produit"""
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'comptoir': product.stock_comptoir,
        'ingredients_local': product.stock_ingredients_local,
        'ingredients_magasin': product.stock_ingredients_magasin,
        'consommables': product.stock_consommables,
        'total': product.total_stock_all_locations,
        'low_stock_locations': product.get_low_stock_locations()
    })

@stock.route('/api/movements_history/<int:product_id>')
@login_required
def api_movements_history(product_id):
    """API pour l'historique des mouvements d'un produit"""
    movements = StockMovement.query.filter_by(product_id=product_id)\
        .order_by(StockMovement.created_at.desc())\
        .limit(20).all()
    
    movements_data = []
    for movement in movements:
        movements_data.append({
            'reference': movement.reference,
            'date': movement.created_at.strftime('%d/%m/%Y %H:%M'),
            'type': movement.movement_type.value,
            'location': movement.stock_location.value,
            'quantity': movement.quantity,
            'stock_after': movement.stock_after,
            'reason': movement.reason,
            'user': movement.user.username if movement.user else 'N/A'
        })
    
    return jsonify(movements_data)
