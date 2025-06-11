from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
csrf = CSRFProtect()

login.login_view = 'login'
login.login_message_category = 'info'
login.login_message = "Veuillez vous connecter pour accéder à cette page."