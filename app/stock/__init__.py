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

# Import des routes après création du blueprint pour éviter les imports circulaires
from . import routes
