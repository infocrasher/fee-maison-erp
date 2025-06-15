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
    
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que la commande peut être marquée comme reçue
    if not order.can_be_received_at_shop():
        flash(f"La commande #{order_id} ne peut pas être marquée comme reçue. Statut actuel: {order.get_status_display()}", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    # Récupérer les employés sélectionnés depuis le formulaire
    employee_ids = request.form.getlist('employee_ids[]')
    
    if not employee_ids:
        # Si pas d'employés fournis, rediriger vers le formulaire de sélection
        return redirect(url_for('status.select_employees_for_status_change', 
                              order_id=order_id, 
                              new_status='ready_at_shop'))
    
    try:
        # Marquer la commande comme reçue au magasin
        if order.mark_as_received_at_shop():
            
            # Assigner les employés qui ont produit cette commande
            for employee_id in employee_ids:
                employee = Employee.query.get(employee_id)
                if employee and employee.is_active:
                    order.assign_producer(employee)
            
            db.session.commit()
            
            producers_names = ", ".join([emp.name for emp in order.produced_by])
            flash(f'Commande #{order_id} marquée comme reçue au magasin. Produite par: {producers_names}', 'success')
            
        else:
            flash(f"Erreur lors du changement de statut de la commande #{order_id}", 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la mise à jour: {str(e)}", 'error')
    
    return redirect(url_for('dashboard.shop_dashboard'))

@status_bp.route('/<int:order_id>/change-status-to-delivered', methods=['POST'])
@login_required
@admin_required
def change_status_to_delivered(order_id):
    """Change le statut de 'ready_at_shop' à 'delivered' pour commandes client"""
    
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que c'est une commande client
    if order.order_type != 'customer_order':
        flash(f"Seules les commandes client peuvent être marquées comme livrées", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    # Vérifier que la commande peut être livrée
    if not order.can_be_delivered():
        flash(f"La commande #{order_id} ne peut pas être livrée. Statut actuel: {order.get_status_display()}", 'error')
        return redirect(url_for('dashboard.shop_dashboard'))
    
    try:
        # Marquer comme livrée (décrémente le stock automatiquement)
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
    
    # Récupérer les employés actifs de production
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
            # Changement de statut direct
            old_status = order.status
            order.status = new_status
            
            # Assigner les employés si fournis
            if employee_ids:
                # Supprimer les anciens producteurs
                order.produced_by.clear()
                
                # Ajouter les nouveaux
                for employee_id in employee_ids:
                    employee = Employee.query.get(employee_id)
                    if employee and employee.is_active:
                        order.assign_producer(employee)
            
            # Ajouter une note du changement
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
    
    # GET - Afficher le formulaire
    employees = Employee.query.filter(
        Employee.is_active == True
    ).order_by(Employee.name).all()
    
    return render_template('orders/manual_status_form.html',
                         order=order,
                         employees=employees,
                         title=f"Changement Statut - Commande #{order_id}")

# API pour récupérer les employés actifs
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

@status_bp.route('/<int:order_id>/test-employees/<string:new_status>')
def test_employees_no_decorators(order_id, new_status):
    """Test sans décorateurs pour isoler le problème"""
    return f"✅ TEST OK: order_id={order_id}, new_status={new_status}"

# Test 1: Seulement login_required
@status_bp.route('/<int:order_id>/test-login/<string:new_status>')
@login_required
def test_login_only(order_id, new_status):
    return f"✅ LOGIN OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"

# Test 2: Seulement admin_required
@status_bp.route('/<int:order_id>/test-admin/<string:new_status>')
@admin_required
def test_admin_only(order_id, new_status):
    return f"✅ ADMIN OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"

@status_bp.route('/<int:order_id>/test-both/<string:new_status>')
@login_required
@admin_required
def test_both_decorators(order_id, new_status):
    return f"✅ BOTH OK: order_id={order_id}, new_status={new_status}, user={current_user.username}"