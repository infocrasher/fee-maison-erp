# -*- coding: utf-8 -*-
"""
app/employees/models.py
Modèle Employee pour le tracking de production ERP Fée Maison
"""

from datetime import datetime
from decimal import Decimal
from extensions import db

# Table de liaison pour les collaborations (plusieurs employés par commande)
order_employees = db.Table('order_employees',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('employees.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='production')
    salaire_fixe = db.Column(db.Numeric(10, 2))
    prime = db.Column(db.Numeric(10, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relations - Utilisation de chaînes pour éviter imports circulaires
    orders_produced = db.relationship('Order', secondary=order_employees, back_populates='produced_by')
    
    def get_monthly_revenue(self, year, month):
        """Calcule le CA généré par cet employé pour un mois donné"""
        # Import local pour éviter la circularité
        from models import Order
        
        orders = Order.query.filter(
            Order.produced_by.contains(self),
            db.extract('year', Order.due_date) == year,
            db.extract('month', Order.due_date) == month,
            Order.status.in_(['delivered', 'completed'])
        ).all()
        
        return sum(float(order.total_amount or 0) for order in orders)
    
    def get_productivity_score(self, year, month):
        """Calcule le score de productivité (CA / salaire)"""
        revenue = self.get_monthly_revenue(year, month)
        total_salary = float(self.salaire_fixe or 0) + float(self.prime or 0)
        
        if total_salary > 0:
            return revenue / total_salary
        return 0
    
    def get_orders_count(self, year=None, month=None):
        """Compte le nombre de commandes produites"""
        if year and month:
            # Import local pour éviter la circularité
            from models import Order
            from sqlalchemy import extract  # ← Import nécessaire
            
            count = Order.query.filter(
                Order.produced_by.contains(self),
                extract('year', Order.due_date) == year,
                extract('month', Order.due_date) == month
            ).count()
            return count
        else:
            # Sans filtre, on compte directement
            return len(self.orders_produced)

    
    def get_total_salary(self):
        """Retourne le salaire total (fixe + prime)"""
        return float(self.salaire_fixe or 0) + float(self.prime or 0)
    
    def get_formatted_salary(self):
        """Retourne le salaire formaté"""
        total = self.get_total_salary()
        return f"{total:.2f} DA"
    
    def is_production_staff(self):
        """Vérifie si l'employé fait partie de l'équipe de production"""
        return self.role in ['production', 'chef_production', 'assistant_production']
    
    def __repr__(self):
        return f'<Employee {self.name}>'
