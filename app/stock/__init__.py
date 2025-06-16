"""
Blueprint Stock - Module de gestion des 4 stocks
Module: app/stock
Auteur: ERP Fée Maison
"""

from flask import Blueprint

# Import critique des modèles pour qu'Alembic les détecte
from . import models

# Création du blueprint stock
bp = Blueprint('stock', __name__, url_prefix='/stock')

# CORRECTION CRITIQUE : Import automatique des routes dès la création du blueprint
# Ceci évite l'erreur "blueprint already registered" en important les routes 
# AVANT l'enregistrement du blueprint dans l'application
from . import routes
