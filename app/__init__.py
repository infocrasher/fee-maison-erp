import os
from flask import Flask, url_for
from config import config_by_name
from extensions import db, migrate, login
from datetime import datetime
from flask_wtf.csrf import generate_csrf # <-- Importer la fonction

def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    login.login_view = 'auth.login'
    login.login_message_category = 'info'
    login.login_message = "Veuillez vous connecter pour accéder à cette page."

    from models import User
    @login.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # --- PROCESSEURS DE CONTEXTE POUR LES VARIABLES GLOBALES ---
    @app.context_processor
    def inject_global_variables():
        # Dictionnaire contenant toutes les variables/fonctions à rendre disponibles
        return dict(
            # Rend la fonction csrf_token() disponible sous le nom 'csrf_token'
            csrf_token=generate_csrf,
            # Vous pouvez garder ce nom si vous le préférez
            manual_csrf_token=generate_csrf 
        )
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convertit les retours à la ligne en <br>"""
        if not text:
            return text
        from markupsafe import Markup
        return Markup(text.replace('\n', '<br>'))
    # Enregistrement des Blueprints
    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.products.routes import products as products_blueprint
    app.register_blueprint(products_blueprint, url_prefix='/admin/products')

    from app.orders.routes import orders as orders_blueprint
    app.register_blueprint(orders_blueprint, url_prefix='/admin/orders')

    from app.recipes.routes import recipes as recipes_blueprint
    app.register_blueprint(recipes_blueprint, url_prefix='/admin/recipes')
    
    from app.stock.routes import stock as stock_blueprint
    app.register_blueprint(stock_blueprint, url_prefix='/admin/stock')

    from app.admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')


    # Commande CLI pour créer un admin
    @app.cli.command("create-admin")
    def create_admin():
        if User.query.filter_by(email="admin@example.com").first():
            print("L'utilisateur admin existe déjà.")
            return
        admin_user = User(username="admin", email="admin@example.com", role='admin')
        admin_user.set_password("password123")
        db.session.add(admin_user)
        db.session.commit()
        print("Utilisateur admin créé avec succès.")

    return app