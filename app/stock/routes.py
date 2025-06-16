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
    total_value =
