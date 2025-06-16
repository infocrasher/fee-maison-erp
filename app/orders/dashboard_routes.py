from flask import render_template, jsonify
from flask_login import login_required
from . import dashboard_bp
from models import Order, Product
from app.employees.models import Employee
from datetime import datetime, timedelta
from decorators import admin_required

@dashboard_bp.route('/production')
@login_required
@admin_required
def production_dashboard():
    """Dashboard de production pour Rayan"""
    # Commandes en production
    orders_in_production = Order.query.filter(
        Order.status == 'in_production'
    ).order_by(Order.due_date.asc()).all()
    
    # Commandes en attente
    orders_pending = Order.query.filter(
        Order.status == 'pending'
    ).order_by(Order.due_date.asc()).all()
    
    return render_template('dashboards/production_dashboard.html',
                         orders_in_production=orders_in_production,
                         orders_pending=orders_pending,
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
    
    # Commandes prêtes à livrer
    orders_ready = Order.query.filter(
        Order.status == 'ready_at_shop'
    ).order_by(Order.due_date.asc()).all()
    
    return render_template('dashboards/shop_dashboard.html',
                         orders_in_production=orders_in_production,
                         orders_ready=orders_ready,
                         title="Dashboard Magasin")

@dashboard_bp.route('/ingredients-alerts')
@login_required
@admin_required
def ingredients_alerts():
    """Dashboard alertes ingrédients pour Amel - Gestion des achats"""
    
    # Ingrédients avec stock bas (selon quantity_in_stock existant)
    low_stock_ingredients = Product.query.filter(
        Product.product_type == 'ingredient',
        Product.quantity_in_stock <= 5
    ).order_by(Product.name.asc()).all()
    
    # Ingrédients en rupture
    out_of_stock_ingredients = Product.query.filter(
        Product.product_type == 'ingredient',
        Product.quantity_in_stock <= 0
    ).order_by(Product.name.asc()).all()
    
    return render_template('dashboards/ingredients_alerts.html',
                         low_stock_ingredients=low_stock_ingredients,
                         out_of_stock_ingredients=out_of_stock_ingredients,
                         title="Alertes Ingrédients")

@dashboard_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Dashboard administrateur principal"""
    
    # Statistiques générales
    today = datetime.now().date()
    
    # Commandes du jour
    orders_today = Order.query.filter(
        Order.created_at >= today
    ).count()
    
    # Employés actifs
    active_employees = Employee.query.filter(Employee.is_active == True).count()
    
    # Produits en stock bas
    low_stock_count = Product.query.filter(Product.quantity_in_stock <= 5).count()
    
    # Commandes en retard
    overdue_orders = Order.query.filter(
        Order.due_date < datetime.utcnow(),
        Order.status.in_(['pending', 'in_production'])
    ).count()
    
    return render_template('dashboards/admin_dashboard.html',
                         orders_today=orders_today,
                         active_employees=active_employees,
                         low_stock_count=low_stock_count,
                         overdue_orders=overdue_orders,
                         title="Dashboard Administrateur")

@dashboard_bp.route('/sales')
@login_required
@admin_required
def sales_dashboard():
    """Dashboard des ventes"""
    
    # Commandes livrées ce mois
    current_month = datetime.now().replace(day=1)
    
    delivered_orders = Order.query.filter(
        Order.status == 'delivered',
        Order.updated_at >= current_month
    ).count()
    
    return render_template('dashboards/sales_dashboard.html',
                         delivered_orders=delivered_orders,
                         title="Dashboard Ventes")

@dashboard_bp.route('/api/orders-stats')
@login_required
@admin_required
def orders_stats_api():
    """API pour statistiques des commandes en temps réel"""
    
    stats = {
        'pending': Order.query.filter_by(status='pending').count(),
        'in_production': Order.query.filter_by(status='in_production').count(),
        'ready_at_shop': Order.query.filter_by(status='ready_at_shop').count(),
        'delivered': Order.query.filter_by(status='delivered').count()
    }
    
    return jsonify(stats)
