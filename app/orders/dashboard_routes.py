from flask import render_template, jsonify, Blueprint
from flask_login import login_required
from models import Order, Product
from app.employees.models import Employee
from datetime import datetime, timedelta
from decorators import admin_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/production')
@login_required
@admin_required
def production_dashboard():
    """Dashboard de production pour Rayan"""
    
    # ### DEBUT DE LA CORRECTION ###
    # On récupère toutes les commandes qui doivent être produites
    # C'est-à-dire celles "En attente" ET "En production"
    orders_to_produce = Order.query.filter(
        Order.status.in_(['pending', 'in_production'])
    ).order_by(Order.due_date.asc()).all()
    # ### FIN DE LA CORRECTION ###
    
    # Calcul des stats pour l'en-tête (basé sur la nouvelle requête)
    now = datetime.utcnow()
    orders_on_time = 0
    orders_soon = 0
    orders_overdue = 0
    for order in orders_to_produce:
        if order.due_date:
            time_diff_hours = (order.due_date - now).total_seconds() / 3600
            if time_diff_hours < 0:
                orders_overdue += 1
            elif time_diff_hours < 2:
                orders_soon += 1
            else:
                orders_on_time += 1
    
    return render_template('dashboards/production_dashboard.html',
                         orders=orders_to_produce,  # On passe la bonne variable au template
                         orders_on_time=orders_on_time,
                         orders_soon=orders_soon,
                         orders_overdue=orders_overdue,
                         total_orders=len(orders_to_produce),
                         title="Dashboard Production")

# ... (le reste de tes routes de dashboard reste identique)
@dashboard_bp.route('/shop')
@login_required
@admin_required
def shop_dashboard():
    orders_in_production = Order.query.filter(
        Order.status == 'in_production'
    ).order_by(Order.due_date.asc()).all()
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
    low_stock_ingredients = Product.query.filter(
        Product.product_type == 'ingredient',
        Product.quantity_in_stock <= 5
    ).order_by(Product.name.asc()).all()
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
    today = datetime.now().date()
    orders_today = Order.query.filter(
        Order.created_at >= today
    ).count()
    active_employees = Employee.query.filter(Employee.is_active == True).count()
    low_stock_count = Product.query.filter(Product.quantity_in_stock <= 5).count()
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
    stats = {
        'pending': Order.query.filter_by(status='pending').count(),
        'in_production': Order.query.filter_by(status='in_production').count(),
        'ready_at_shop': Order.query.filter_by(status='ready_at_shop').count(),
        'delivered': Order.query.filter_by(status='delivered').count()
    }
    return jsonify(stats)