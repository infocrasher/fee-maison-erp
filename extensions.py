# fee_maison_gestion/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()