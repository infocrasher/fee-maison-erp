from flask import Blueprint

# ✅ CORRECTION : Enlever url_prefix pour laisser app/__init__.py le gérer
bp = Blueprint('stock', __name__)

from app.stock import routes
