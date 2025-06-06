# tests/test_app.py
from flask import url_for

def test_home_page(client, app):
    """Teste si la page d'accueil se charge correctement."""
    with app.test_request_context():
        response = client.get(url_for('hello_world'))
    assert response.status_code == 200
    assert "Bienvenue chez Fée Maison" in response.data.decode('utf-8')

def test_login_page_loads(client, app):
    """Teste si la page de connexion se charge correctement."""
    with app.test_request_context():
        response = client.get(url_for('login'))
    assert response.status_code == 200
    assert "Connexion" in response.data.decode('utf-8')

def test_register_page_loads(client, app):
    """Teste si la page d'inscription se charge correctement."""
    with app.test_request_context():
        response = client.get(url_for('register'))
    assert response.status_code == 200
    assert "Inscription" in response.data.decode('utf-8')

def test_dashboard_unauthorized_redirects_to_login(client, app):
    """Teste si l'accès au dashboard sans être connecté redirige vers la page de login."""
    with app.test_request_context():
        response_no_redirect = client.get(url_for('dashboard'), follow_redirects=False)
        expected_login_url_path = url_for('login')
    assert response_no_redirect.status_code == 302
    assert expected_login_url_path in response_no_redirect.location

    with app.test_request_context():
        response_redirected = client.get(url_for('dashboard'), follow_redirects=True)
    assert response_redirected.status_code == 200
    assert "Connexion" in response_redirected.data.decode('utf-8')