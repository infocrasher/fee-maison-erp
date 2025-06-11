import os
from flask import Flask
from config import config_by_name
from extensions import db, migrate, login

def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'
    app.config.from_object(config_by_name[config_name])

    # Lier les extensions à l'application
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Configuration de Flask-Login
    login.login_view = 'auth.login'
    login.login_message_category = 'info'
    login.login_message = "Veuillez vous connecter pour accéder à cette page."

    from models import User
    @login.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Enregistrement des Blueprints
    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # (Plus tard, on ajoutera les autres blueprints ici)

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