import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32) 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    POSTS_PER_PAGE = 10
    ORDERS_PER_PAGE = 10
    PRODUCTS_PER_PAGE = 10
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

class DevelopmentConfigSQLite(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = True
    SQLITE_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fee_maison.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL_SQLITE') or \
        f'sqlite:///{SQLITE_DB_PATH}'

class DevelopmentConfigPostgreSQL(Config):
    DEBUG = True
    POSTGRES_USER = os.environ.get('POSTGRES_USER_DEV') or 'fee_maison_user'
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD_DEV') or 'votre_mot_de_passe_ici_a_remplacer' # VÉRIFIEZ CECI
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST_DEV') or 'localhost'
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT_DEV') or '5432'
    POSTGRES_DB_NAME = os.environ.get('POSTGRES_DB_DEV') or 'fee_maison_db'
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_NAME}"

class TestingConfig(Config):
    TESTING = True
    DEBUG = True 
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:' 
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False

class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    TESTING = False
    
    # Récupérer les variables d'environnement au niveau de la classe
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
    POSTGRES_DB_NAME = os.environ.get('POSTGRES_DB_NAME')

    # Construire l'URI. La vérification se fera si FLASK_ENV est 'production'
    # lors de la sélection de la configuration dans app.py
    if POSTGRES_USER and POSTGRES_PASSWORD and POSTGRES_HOST and POSTGRES_PORT and POSTGRES_DB_NAME:
        SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_NAME}"
    else:
        # Si nous sommes en train de charger ce fichier (par exemple, pour `flask db`),
        # et que FLASK_ENV n'est pas 'production', nous ne voulons pas d'erreur ici.
        # Nous mettons une valeur placeholder ou None. L'erreur sera levée dans create_app si on essaie d'utiliser cette config.
        SQLALCHEMY_DATABASE_URI = None 
        # La vérification réelle que ces variables sont définies pour la production
        # devrait idéalement se faire au moment où l'application est configurée
        # avec ProductionConfig dans create_app.

# Dictionnaire pour accéder aux configurations par leur nom.
config_by_name = dict(
    development=DevelopmentConfigPostgreSQL,
    testing=TestingConfig,
    production=ProductionConfig,
    sqlite_dev=DevelopmentConfigSQLite,
    default=DevelopmentConfigPostgreSQL
)

# Ajout d'une vérification dans la fonction create_app (dans app.py) serait plus robuste
# pour la ProductionConfig.
# Pour l'instant, cette modification de config.py devrait suffire pour que `flask db migrate` fonctionne.