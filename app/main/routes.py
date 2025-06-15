# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Order, Product, Recipe  # ✅ CORRECTION : Recipe est dans models.py principal
from app.employees.models import Employee    # ✅ Seul Employee est dans un module séparé
from datetime import datetime, date
from extensions import db

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def hello_world():
    return render_template('main/home.html', title="Accueil")

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal avec statistiques"""
    
    # Calcul des statistiques pour l'affichage
    today = date.today()
    
    # Compter les commandes d'aujourd'hui
    orders_today = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    
    # Compter les employés actifs
    employees_count = Employee.query.filter(Employee.is_active == True).count()
    
    # Compter les produits
    products_count = Product.query.count()
    
    # Compter les recettes
    recipes_count = Recipe.query.count()
    
    return render_template('main/dashboard.html', 
                         title="Tableau de Bord",
                         orders_today=orders_today,
                         employees_count=employees_count,
                         products_count=products_count,
                         recipes_count=recipes_count)
