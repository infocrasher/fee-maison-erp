from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import Order, User, Product
from decorators import admin_required
from sqlalchemy import func

# Blueprint pour les dashboards
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/admin')
@login_required  
@admin_required
def admin_dashboard():
    """Dashboard administrateur avec vue d'ensemble"""
    try:
        from models import Order, Product, User
        from app.employees.models import Employee
        
        # Statistiques générales
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        total_products = Product.query.count()
        total_users = User.query.count()
        total_employees = Employee.query.count()
        
        # Commandes récentes
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        # Commandes du jour
        today = datetime.utcnow().date()
        today_orders = Order.query.filter(
            func.date(Order.due_date) == today
        ).all()
        
        return render_template('dashboards/admin_dashboard.html',
                             total_orders=total_orders,
                             pending_orders=pending_orders,
                             total_products=total_products,
                             total_users=total_users,
                             total_employees=total_employees,
                             recent_orders=recent_orders,
                             today_orders=today_orders,
                             title="Dashboard Administrateur")
                             
    except Exception as e:
        flash(f'Erreur lors du chargement du dashboard: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

@dashboard_bp.route('/production')
@login_required
def production_dashboard():
    """Dashboard de production pour Rayan"""
    try:
        # Commandes en production ou à produire
        production_orders = Order.query.filter(
            Order.status.in_(['pending', 'in_production'])
        ).order_by(Order.due_date.asc()).all()
        
        # Statistiques de production
        total_in_production = len(production_orders)
        urgent_orders = [o for o in production_orders if o.is_overdue()]
        
        return render_template('dashboards/production_dashboard.html',
                             production_orders=production_orders,
                             total_in_production=total_in_production,
                             urgent_orders=urgent_orders,
                             title="Dashboard Production")
                             
    except Exception as e:
        flash(f'Erreur lors du chargement du dashboard production: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

@dashboard_bp.route('/sales')
@login_required
def sales_dashboard():
    """Dashboard des ventes pour Yasmine"""
    try:
        # Commandes prêtes pour livraison/vente
        ready_orders = Order.query.filter_by(status='ready_at_shop').all()
        
        # Commandes en livraison
        delivery_orders = Order.query.filter_by(status='out_for_delivery').all()
        
        return render_template('dashboards/sales_dashboard.html',
                             ready_orders=ready_orders,
                             delivery_orders=delivery_orders,
                             title="Dashboard Ventes")
                             
    except Exception as e:
        flash(f'Erreur lors du chargement du dashboard ventes: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

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
    }  # ← CORRECTION : Accolade fermante ajoutée

    for order in orders:
        time_diff = (order.due_date - now).total_seconds() / 3600
        if time_diff < 0 or time_diff < 0.5:
            stats['overdue'] += 1
        elif time_diff < 2:
            stats['soon'] += 1
        else:
            stats['on_time'] += 1

    return jsonify(stats)

# CORRECTION : Alias pour compatibilité avec app/__init__.py
dashboard = dashboard_bp
