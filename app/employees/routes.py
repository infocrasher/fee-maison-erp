# -*- coding: utf-8 -*-
"""
app/employees/routes.py
Routes pour la gestion des employés
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db
from app.employees.models import Employee
from app.employees.forms import EmployeeForm, EmployeeSearchForm
from decorators import admin_required
from datetime import datetime

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@login_required
@admin_required
def list_employees():
    """Liste des employés avec recherche et filtres"""
    
    form = EmployeeSearchForm()
    
    # Query de base
    query = Employee.query
    
    # Filtres de recherche
    if form.search.data:
        search_term = f"%{form.search.data}%"
        query = query.filter(Employee.name.ilike(search_term))
    
    if form.role_filter.data:
        query = query.filter(Employee.role == form.role_filter.data)
    
    if form.status_filter.data == 'active':
        query = query.filter(Employee.is_active == True)
    elif form.status_filter.data == 'inactive':
        query = query.filter(Employee.is_active == False)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    employees_pagination = query.order_by(Employee.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter(Employee.is_active == True).count()
    production_staff = Employee.query.filter(
        Employee.is_active == True,
        Employee.role.in_(['production', 'chef_production', 'assistant_production', 'patissier'])
    ).count()
    
    return render_template('employees/list_employees.html',
                         employees_pagination=employees_pagination,
                         form=form,
                         total_employees=total_employees,
                         active_employees=active_employees,
                         production_staff=production_staff,
                         title="Gestion des Employés")

@employees_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_employee():
    """Créer un nouvel employé"""
    
    form = EmployeeForm()
    
    if form.validate_on_submit():
        try:
            employee = Employee(
                name=form.name.data,
                role=form.role.data,
                salaire_fixe=form.salaire_fixe.data,
                prime=form.prime.data or 0,
                is_active=form.is_active.data,
                notes=form.notes.data
            )
            
            db.session.add(employee)
            db.session.commit()
            
            flash(f'Employé "{employee.name}" créé avec succès !', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création : {str(e)}', 'error')
    
    return render_template('employees/employee_form.html',
                         form=form,
                         title="Nouvel Employé",
                         action="Créer")

@employees_bp.route('/<int:employee_id>')
@login_required
@admin_required
def view_employee(employee_id):
    """Voir les détails d'un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Statistiques de performance
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    monthly_revenue = employee.get_monthly_revenue(current_year, current_month)
    productivity_score = employee.get_productivity_score(current_year, current_year)
    orders_count = employee.get_orders_count(current_year, current_month)
    
    return render_template('employees/view_employee.html',
                         employee=employee,
                         monthly_revenue=monthly_revenue,
                         productivity_score=productivity_score,
                         orders_count=orders_count,
                         title=f"Employé - {employee.name}")

@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_employee(employee_id):
    """Modifier un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(employee)
            db.session.commit()
            
            flash(f'Employé "{employee.name}" modifié avec succès !', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'error')
    
    return render_template('employees/employee_form.html',
                         form=form,
                         employee=employee,
                         title=f"Modifier - {employee.name}",
                         action="Modifier")

@employees_bp.route('/<int:employee_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_employee_status(employee_id):
    """Activer/désactiver un employé"""
    
    employee = Employee.query.get_or_404(employee_id)
    
    try:
        employee.is_active = not employee.is_active
        db.session.commit()
        
        status = "activé" if employee.is_active else "désactivé"
        flash(f'Employé "{employee.name}" {status} avec succès !', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du changement de statut : {str(e)}', 'error')
    
    return redirect(url_for('employees.view_employee', employee_id=employee_id))

# API pour les dashboards
@employees_bp.route('/api/production-staff')
@login_required
@admin_required
def get_production_staff():
    """API pour récupérer les employés de production actifs"""
    
    employees = Employee.query.filter(
        Employee.is_active == True,
        Employee.role.in_(['production', 'chef_production', 'assistant_production', 'patissier'])
    ).order_by(Employee.name).all()
    
    return jsonify([{
        'id': emp.id,
        'name': emp.name,
        'role': emp.role,
        'role_display': emp.role.replace('_', ' ').title()
    } for emp in employees])

@employees_bp.route('/api/stats')
@login_required
@admin_required
def get_employees_stats():
    """API pour les statistiques employés"""
    
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    employees = Employee.query.filter(Employee.is_active == True).all()
    
    stats = []
    for emp in employees:
        stats.append({
            'id': emp.id,
            'name': emp.name,
            'role': emp.role,
            'monthly_revenue': emp.get_monthly_revenue(current_year, current_month),
            'productivity_score': emp.get_productivity_score(current_year, current_month),
            'orders_count': emp.get_orders_count(current_year, current_month),
            'total_salary': emp.get_total_salary()
        })
    
    return jsonify(stats)
