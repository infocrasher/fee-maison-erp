# tests/conftest.py
import pytest
import sys
import os
from flask import url_for

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, User, Category # Importer Category aussi si utilisé dans une fixture
from extensions import db as _db

@pytest.fixture(scope='session')
def app():
    """Crée une instance de l'application Flask pour la session de test."""
    current_app = create_app(config_name='testing')
    
    ctx = current_app.app_context()
    ctx.push()

    yield current_app

    ctx.pop()

@pytest.fixture(scope='function') # Changé en function pour une isolation complète par test
def db_session(app): # Dépend de la fixture 'app' de scope session
    """Crée les tables, fournit la session, et nettoie après chaque test."""
    with app.app_context(): # Contexte nécessaire pour _db.create_all() et _db.drop_all()
        _db.create_all() # Crée les tables au début de chaque test
        
        yield _db.session # Fournit la session pour le test

        # Nettoyage après chaque test
        _db.session.remove() # Important pour s'assurer que la session est fermée
        _db.drop_all()   # Supprime toutes les tables pour le prochain test
                         # Assure une base de données fraîche pour chaque fonction de test.

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def regular_user(db_session): # Dépend de db_session
    """Crée un utilisateur régulier pour les tests."""
    # La fixture db_session s'exécute dans un app_context et gère create/drop all.
    # Nous pouvons donc directement utiliser db_session ici.
    existing_user = User.query.filter_by(email='user@example.com').first() # .query utilise la session implicite
    if existing_user:
        return existing_user # Retourner l'existant si déjà créé dans ce scope de test (ne devrait pas arriver avec scope function pour db_session)
            
    user = User(username='regularuser', email='user@example.com', role='user')
    user.set_password('userpassword')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope='function')
def admin_user(db_session): # Dépend de db_session
    """Crée un utilisateur admin pour les tests."""
    existing_admin = User.query.filter_by(email='admin@example.com').first()
    if existing_admin:
        return existing_admin
            
    admin = User(username='adminuser', email='admin@example.com', role='admin')
    admin.set_password('adminpassword')
    db_session.add(admin)
    db_session.commit()
    return admin

@pytest.fixture(scope='function')
def regular_client(client, regular_user, app):
    """Un client de test connecté en tant qu'utilisateur régulier."""
    with app.test_request_context():
        client.post(url_for('login'), data={
            'email': regular_user.email,
            'password': 'userpassword'
        }, follow_redirects=True)
    return client

@pytest.fixture(scope='function')
def admin_client(client, admin_user, app):
    """Un client de test connecté en tant qu'utilisateur admin."""
    with app.test_request_context():
        client.post(url_for('login'), data={
            'email': admin_user.email,
            'password': 'adminpassword'
        }, follow_redirects=True)
    return client