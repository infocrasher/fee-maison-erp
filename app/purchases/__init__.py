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

# IMPORTANT : Les routes seront importées dans app/__init__.py
# après l'enregistrement du blueprint pour éviter les imports circulaires
