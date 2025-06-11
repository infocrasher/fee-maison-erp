# Fichier: app/admin/routes.py

from flask import Blueprint, render_template
from flask_login import login_required
from decorators import admin_required

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Vous pouvez ajouter ici la logique pour collecter des données pour le dashboard admin
    return render_template('admin/admin_dashboard.html', title='Administration')