# -*- coding: utf-8 -*-
"""
app/employees/forms.py
Formulaires pour la gestion des employés
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class EmployeeForm(FlaskForm):
    name = StringField('Nom complet', validators=[
        DataRequired(message="Le nom est obligatoire"),
        Length(min=2, max=100, message="Le nom doit contenir entre 2 et 100 caractères")
    ])
    
    role = SelectField('Rôle', choices=[
        ('production', 'Employé Production'),
        ('chef_production', 'Chef de Production'),
        ('assistant_production', 'Assistant Production'),
        ('patissier', 'Pâtissier'),
        ('apprenti', 'Apprenti'),
        ('manager', 'Manager'),
        ('vendeur', 'Vendeur')
    ], validators=[DataRequired(message="Veuillez sélectionner un rôle")])
    
    salaire_fixe = DecimalField('Salaire fixe (DA)', validators=[
        Optional(),
        NumberRange(min=0, max=999999, message="Le salaire doit être positif")
    ], places=2)
    
    prime = DecimalField('Prime (DA)', validators=[
        Optional(),
        NumberRange(min=0, max=999999, message="La prime doit être positive")
    ], places=2, default=0)
    
    is_active = BooleanField('Employé actif', default=True)
    
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=500, message="Les notes ne doivent pas dépasser 500 caractères")
    ])

class EmployeeSearchForm(FlaskForm):
    search = StringField('Rechercher un employé', validators=[Optional()])
    
    role_filter = SelectField('Filtrer par rôle', choices=[
        ('', 'Tous les rôles'),
        ('production', 'Production'),
        ('chef_production', 'Chef de Production'),
        ('assistant_production', 'Assistant Production'),
        ('patissier', 'Pâtissier'),
        ('apprenti', 'Apprenti'),
        ('manager', 'Manager'),
        ('vendeur', 'Vendeur')
    ], validators=[Optional()])
    
    status_filter = SelectField('Filtrer par statut', choices=[
        ('', 'Tous'),
        ('active', 'Actifs seulement'),
        ('inactive', 'Inactifs seulement')
    ], validators=[Optional()])
