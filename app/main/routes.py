from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def hello_world():
    return render_template('main/home.html', title='Accueil')

@main.route('/dashboard')
def dashboard():
    # Mettez ici la logique du dashboard que nous avions avant
    return render_template('main/dashboard.html', title='Tableau de Bord')