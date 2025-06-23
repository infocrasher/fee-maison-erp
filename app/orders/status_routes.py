# -*- coding: utf-8 -*-
"""
Status routes pour ERP Fée Maison
Routes spécialisées pour les changements de statut avec sélection employés
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Order, db
from app.employees.models import Employee
from decorators import admin_required

# Blueprint pour les changements de statut
status_bp = Blueprint('status', __name__)

@status_bp.route('/<int:order_id>/change-status-to-ready', methods=['POST'])
@login_required
@admin_required
def change_status_to_ready(order_id):
    """Change le statut de 'in_production' à 'ready_at_shop' avec sélection employé"""
    
    # ### DEBUT DE LA CORRECTION ###
    # On importe les modèles nécessaires ici pour éviter les dépendances circulaires
    from models import Product, Recipe
    # ### FIN DE LA CORRECTION ###

    order = Order.query.get_or_404(order_id)
    
    if not order.can_be_received_at_shop():
        flash(f"La commande #{order_id} ne peut pas être marquée comme reçue. Statut actuel: {order.get_status_display()}", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    employee_ids = request.form.getlist('employee_ids[]')
    
    if not employee_ids:
        return redirect(url_for('status.select_employees_for_status_change', 
                              order_id=order_id, 
                              new_status='ready_at_shop'))
    
    try:
        # ### DEBUT DE LA NOUVELLE LOGIQUE DE STOCK ###
        # Étape 1 : Décrémenter les ingrédients
        for order_item in order.items:
            product_fini = order_item.product
            # On ne décrémente que si le produit fini a une recette associée
            if product_fini and product_fini.recipe_definition:
                recipe = product_fini.recipe_definition
                # On récupère le labo de production depuis la recette
                labo_key = recipe.production_location
                
                # On parcourt les ingrédients de la recette
                for ingredient_in_recipe in recipe.ingredients:
                    ingredient_product = ingredient_in_recipe.product
                    # Quantité nécessaire pour 1 produit fini * quantité commandée
                    quantity_to_decrement = float(ingredient_in_recipe.quantity_needed) * float(order_item.quantity)
                    
                    # On utilise notre nouvelle méthode pour mettre à jour le stock du bon labo
                    ingredient_product.update_stock_by_location(labo_key, -quantity_to_decrement)
                    
                    # Log pour débogage (peut être retiré plus tard)
                    print(f"DECREMENT: {quantity_to_decrement} de {ingredient_product.name} du stock {labo_key}")

        # Étape 2 : Incrémenter le stock du produit fini dans le stock de vente ('comptoir')
        # Cette logique est déjà dans ta méthode mark_as_received_at_shop, on s'assure qu'elle est correcte.
        # Il faut vérifier la méthode _increment_shop_stock dans models.py
        
        # ### FIN DE LA NOUVELLE LOGIQUE DE STOCK ###

        # Marquer la commande comme reçue au magasin (ce qui déclenche l'incrémentation du produit fini)
        if order.mark_as_received_at_shop():
            
            # Assigner les employés
            for employee_id in employee_ids:
                employee = Employee.query.get(employee_id)
                if employee and employee.is_active:
                    order.assign_producer(employee)
            
            db.session.commit()
            
            producers_names = ", ".join([emp.name for emp in order.produced_by])
            flash(f'Commande #{order_id} marquée comme reçue. Stock mis à jour. Produite par: {producers_names}', 'success')
            
        else:
            flash(f"Erreur lors du changement de statut de la commande #{order_id}", 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur critique lors de la mise à jour des stocks: {str(e)}", 'error')
    
    return redirect(url_for('dashboard.shop_dashboard'))

@status_bp.route('/<int:order_id>/change-status-to-delivered', methods=['POST'])
@login_required
@admin_required
def change_status_to_delivered(order_id):
    """Change le statut de 'ready_at_shop' à 'delivered' pour commandes client"""
    
    order = Order.query.get_or_404(order_id)
    
    if order.order_type != 'customer_order':
        flash(f"Seules les commandes client peuvent être marquées comme livrées", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    if not order.can_be_delivered():
        flash(f"La commande #{order_id} ne peut pas être livrée. Statut actuel: {order.get_status_display()}", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    try:
        if order.mark_as_delivered():
            db.session.commit()
            flash(f'Commande #{order_id} marquée comme livrée ! Montant encaissé: {order.total_amount:.2f} DA', 'success')
        else:
            flash(f"Erreur lors du changement de statut de la commande #{order_id}", 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la livraison: {str(e)}", 'error')
    
    return redirect(url_for('dashboard.shop_dashboard'))

@status_bp.route('/<int:order_id>/select-employees/<string:new_status>')
@login_required
@admin_required
def select_employees_for_status_change(order_id, new_status):
    """Formulaire de sélection des employés pour changement de statut"""
    
    order = Order.query.get_or_404(order_id)
    
    employees = Employee.query.filter(
        Employee.is_active == True,
        Employee.role.in_(['production', 'chef_production', 'assistant_production'])
    ).order_by(Employee.name).all()
    
    return render_template('orders/change_status_form.html',
                         order=order,
                         employees=employees,
                         new_status=new_status,
                         title=f"Sélection Employés - Commande #{order_id}")
    
@status_bp.route('/<int:order_id>/manual-status-change', methods=['GET', 'POST'])
@login_required
@admin_required
def manual_status_change(order_id):
    """Changement de statut manuel pour cas spéciaux"""
    
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
        new_status = request.form.get('new_status')
        notes = request.form.get('notes', '')
        employee_ids = request.form.getlist('employee_ids[]')
        
        if not new_status:
            flash("Veuillez sélectionner un nouveau statut", 'error')
            return redirect(request.url)
        
        try:
            old_status = order.status
            order.status = new_status
            
            if employee_ids:
                order.produced_by.clear()
                
                for employee_id in employee_ids:
                    employee = Employee.query.get(employee_id)
                    if employee and employee.is_active:
                        order.assign_producer(employee)
            
            if notes:
                if order.notes:
                    order.notes += f"\n[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] {notes}"
                else:
                    order.notes = f"[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] {notes}"
            
            db.session.commit()
            
            producers_info = ""
            if order.produced_by:
                producers_names = ", ".join([emp.name for emp in order.produced_by])
                producers_info = f" (Employés: {producers_names})"
            
            flash(f'Statut de la commande #{order_id} changé de "{old_status}" à "{new_status}"{producers_info}', 'success')
            
            return redirect(url_for('orders.view_order', order_id=order_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors du changement de statut: {str(e)}", 'error')
    
    employees = Employee.query.filter(
        Employee.is_active == True
    ).order_by(Employee.name).all()
    
    return render_template('orders/manual_status_form.html',
                         order=order,
                         employees=employees,
                         title=f"Changement Statut - Commande #{order_id}")

@status_bp.route('/api/active-employees')
@login_required
@admin_required
def get_active_employees():
    """API pour récupérer la liste des employés actifs"""
    
    employees = Employee.query.filter(Employee.is_active == True).order_by(Employee.name).all()
    
    return jsonify([{
        'id': emp.id,
        'name': emp.name,
        'role': emp.role
    } for emp in employees])

# Routes de test (conservées telles quelles)
@status_bp.route('/<int:order_id>/test-employees/<string:new_status>')
def test_employees_no_decorators(order_id, new_status):
    return f"✅ TEST OK: order_id={order_id}, new_status={new_status}"

@status_bp.route('/<int:order_id>/test-login/<string:new_status>')
@login_required
def test_login_only(order_id, new_status):
    return f"✅ LOGIN OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"

@status_bp.route('/<int:order_id>/test-admin/<string:new_status>')
@admin_required
def test_admin_only(order_id, new_status):
    return f"✅ ADMIN OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"

@status_bp.route('/<int:order_id>/test-both/<string:new_status>')
@login_required
@admin_required
def test_both_decorators(order_id, new_status):
    return f"✅ BOTH OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"