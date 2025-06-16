"""
Extensions Flask pour l'ERP Fée Maison
Fichier: extensions.py
Auteur: ERP Fée Maison
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialisation des extensions Flask
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()  # ← CORRECTION : Instance nommée login_manager
csrf = CSRFProtect()

# Configuration du LoginManager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'
