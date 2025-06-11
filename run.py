from app import create_app
from config import config_by_name
import os

# Crée l'application en utilisant la config définie par la variable d'environnement
app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == '__main__':
    app.run()