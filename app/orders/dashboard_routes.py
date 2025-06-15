# -*- coding: utf-8 -*-
"""
Dashboard routes pour ERP Fée Maison
Routes spécialisées pour les dashboards de production et magasin
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from models import Order, db
from app.employees.models import Employee
from decorators import admin_required

# Blueprint pour les dashboards
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/production')
@login_required 
@admin_required
def production_dashboard():
    """Dashboard production pour Rayan - Affiche les commandes en production"""
    
    # Récupérer seulement les commandes qui doivent apparaître dans le dashboard
    orders = Order.query.filter(
        Order.status.in_(['pending', 'in_production']),
        Order.due_date.isnot(None)
    ).order_by(Order.due_date.asc()).all()
    
    # Calculs des statistiques
    now = datetime.utcnow()
    orders_on_time = 0
    orders_soon = 0  # Entre 30min et 2h
    orders_overdue = 0
    
    for order in orders:
        time_diff = (order.due_date - now).total_seconds() / 3600  # en heures
        
        if time_diff < 0:
            orders_overdue += 1
        elif time_diff < 0.5:  # Moins de 30min
            orders_overdue += 1
        elif time_diff < 2:    # Entre 30min et 2h
            orders_soon += 1
        else:                  # Plus de 2h
            orders_on_time += 1
    
    return render_template('dashboards/production_dashboard.html',
                         orders=orders,
                         orders_on_time=orders_on_time,
                         orders_soon=orders_soon,
                         orders_overdue=orders_overdue,
                         total_orders=len(orders),
                         title="Dashboard Production")

@dashboard_bp.route('/shop')
@login_required
@admin_required  
def shop_dashboard():
    """Dashboard magasin pour Yasmine - Gestion des commandes reçues"""
    
    # Commandes en production (pour anticipation)
    orders_in_production = Order.query.filter(
        Order.status == 'in_production'
    ).order_by(Order.due_date.asc()).all()
    
    # ✅ PROBLÈME ICI : Seulement commandes CLIENT
    orders_ready = Order.query.filter(
        Order.status == 'ready_at_shop',
        Order.order_type == 'customer_order'  # ← Ça exclut les ordres de production !
    ).order_by(Order.due_date.asc()).all()
    
    return render_template('dashboards/shop_dashboard.html',
                         orders_in_production=orders_in_production,
                         orders_ready=orders_ready,
                         title="Dashboard Magasin")

@dashboard_bp.route('/ingredients-alerts')
@login_required
@admin_required
def ingredients_alerts():
    """Vue des ingrédients manquants pour Amel"""
    
    # Pour l'instant, logique simplifiée
    # TODO: Implémenter le calcul réel des ingrédients manquants
    # quand le module stock sera développé
    
    missing_ingredients = []
    
    return render_template('dashboards/ingredients_alerts.html',
                         missing_ingredients=missing_ingredients,
                         title="Ingrédients Manquants")

@dashboard_bp.route('/api/orders-stats')
@login_required
@admin_required
def orders_stats_api():
    """API pour récupérer les stats en temps réel"""
    
    orders = Order.query.filter(
        Order.status.in_(['pending', 'in_production']),
        Order.due_date.isnot(None)
    ).all()
    
    now = datetime.utcnow()
    stats = {
        'on_time': 0,
        'soon': 0,
        'overdue': 0,
        'total': len(orders)
    }
    
    for order in orders:
        time_diff = (order.due_date - now).total_seconds() / 3600
        
        if time_diff < 0 or time_diff < 0.5:
            stats['overdue'] += 1
        elif time_diff < 2:
            stats['soon'] += 1
        else:
            stats['on_time'] += 1
    
    return jsonify(stats)
