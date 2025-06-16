"""
Blueprint Purchases - Module de gestion des achats fournisseurs
Module: app/purchases
Auteur: ERP Fée Maison
"""

from flask import Blueprint

# Import critique des modèles pour qu'Alembic les détecte
from . import models

# Création du blueprint purchases
bp = Blueprint('purchases', __name__, url_prefix='/purchases')

# CORRECTION CRITIQUE : Import automatique des routes dès la création du blueprint
# Ceci évite l'erreur "blueprint already registered" en important les routes 
# AVANT l'enregistrement du blueprint dans l'application
from . import routes
