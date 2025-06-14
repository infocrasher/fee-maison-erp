import traceback
import re
from flask import Flask
from werkzeug.routing import Rule

# Adapter ce chemin selon ta structure
from app import create_app

app = create_app()
client = app.test_client()

def is_static(rule: Rule):
    return rule.endpoint == 'static'

def get_routes(app):
    routes = []
    for rule in app.url_map.iter_rules():
        # Ignore static and HEAD/OPTIONS methods
        if is_static(rule):
            continue
        if 'GET' in rule.methods:
            routes.append(rule)
    return routes

def build_url(rule):
    # Essaie de fournir des arguments par défaut pour les variables d'URL
    defaults = {}
    for arg in rule.arguments:
        if "id" in arg:
            defaults[arg] = 1
        elif "slug" in arg:
            defaults[arg] = "test-slug"
        else:
            defaults[arg] = "test"
    try:
        url = rule.rule
        for arg in rule.arguments:
            url = url.replace(f"<{arg}>", str(defaults[arg]))
            url = url.replace(f"<int:{arg}>", str(defaults[arg]))
            url = url.replace(f"<string:{arg}>", str(defaults[arg]))
        return url
    except Exception as e:
        return None

def suggest_endpoint_fix(error_text):
    """Suggestions spécifiques pour les endpoints de Fée Maison"""
    endpoint_fixes = {
        'categories.list_categories': 'products.list_categories',
        'categories.new_category': 'products.new_category',
        'categories.edit_category': 'products.edit_category',
        'stock.list_stock': 'stock.stock_overview',
        'orders.list_orders': 'orders.list_orders',
        'orders.new_order': 'orders.new_order OU orders.new_customer_order OU orders.new_production_order',
        'admin.users': 'auth.account',
        'main.home': 'main.dashboard',
    }
    
    # Extraction de l'endpoint depuis l'erreur BuildError
    build_error_match = re.search(r"Could not build url for endpoint '([^']+)'", error_text)
    if build_error_match:
        broken_endpoint = build_error_match.group(1)
        if broken_endpoint in endpoint_fixes:
            return f"🔧 CORRECTION NÉCESSAIRE: '{broken_endpoint}' → '{endpoint_fixes[broken_endpoint]}'"
        else:
            return f"🔧 Endpoint inconnu: '{broken_endpoint}' - Vérifie qu'il existe bien dans tes routes"
    
    return ""

def suggest_fixes(error_text):
    lines = error_text.splitlines()
    
    # Priorité aux BuildError (endpoints cassés)
    if "werkzeug.routing.exceptions.BuildError" in error_text:
        endpoint_fix = suggest_endpoint_fix(error_text)
        if endpoint_fix:
            return endpoint_fix
        return "❗ Endpoint Flask non trouvé (BuildError). Vérifie le nom de l'endpoint dans url_for et la déclaration de ta route."
    
    # Variables Jinja2 manquantes
    for line in lines:
        if 'jinja2.exceptions.UndefinedError' in line:
            # Extrait le nom de la variable manquante
            m = re.search(r"'([\w_]+)' is undefined", line)
            if m:
                var = m.group(1)
                common_vars = {
                    'render_field': "Importer la macro render_field ou utiliser {{ form.field(...) }}",
                    'title': "Passer 'title' dans render_template(..., title='Mon Titre')",
                    'form': "Passer 'form' dans render_template(..., form=mon_formulaire)",
                    'current_user': "Assure-toi que Flask-Login est bien configuré",
                    'get_flashed_messages': "Importer get_flashed_messages ou utiliser with get_flashed_messages()",
                }
                
                if var in common_vars:
                    return f"❗ Variable Jinja2 manquante: '{var}'.\n   💡 Solution: {common_vars[var]}"
                else:
                    return f"❗ Variable Jinja2 manquante: '{var}'.\n   ➔ Vérifie que tu passes bien '{var}' dans render_template() ou que c'est une variable globale."
            else:
                return f"❗ Variable Jinja2 non définie détectée. Vérifie le contexte passé au template."
    
    return ""

def test_all_routes(app):
    routes = get_routes(app)
    errors = []
    build_errors = []
    jinja_errors = []
    other_errors = []
    
    print(f"🔍 Test de {len(routes)} routes GET...")
    
    for rule in routes:
        url = build_url(rule)
        if not url:
            continue
        
        try:
            response = client.get(url)
            
            # Vérification des erreurs
            error_found = False
            error_message = ""
            
            if response.status_code >= 500:
                error_found = True
                error_message = response.data.decode("utf8", errors="ignore")
            elif b'jinja2.exceptions.UndefinedError' in response.data:
                error_found = True
                error_message = response.data.decode("utf8", errors="ignore")
            elif b'werkzeug.routing.exceptions.BuildError' in response.data:
                error_found = True
                error_message = response.data.decode("utf8", errors="ignore")
            
            if error_found:
                suggestion = suggest_fixes(error_message)
                error_entry = (url, response.status_code, error_message, suggestion, rule.endpoint)
                
                # Catégorisation des erreurs
                if "BuildError" in error_message:
                    build_errors.append(error_entry)
                elif "UndefinedError" in error_message:
                    jinja_errors.append(error_entry)
                else:
                    other_errors.append(error_entry)
                    
        except Exception as e:
            tb = traceback.format_exc()
            suggestion = suggest_fixes(tb)
            other_errors.append((url, 'EXCEPTION', tb, suggestion, rule.endpoint))
    
    return build_errors, jinja_errors, other_errors

def print_errors_by_category(build_errors, jinja_errors, other_errors):
    total_errors = len(build_errors) + len(jinja_errors) + len(other_errors)
    
    print(f"\n{'='*80}")
    print(f"📊 RÉSUMÉ: {total_errors} erreurs détectées")
    print(f"   🔧 BuildError (endpoints cassés): {len(build_errors)}")
    print(f"   🏷️  Jinja2 (variables manquantes): {len(jinja_errors)}")
    print(f"   ❌ Autres erreurs: {len(other_errors)}")
    print(f"{'='*80}\n")
    
    if build_errors:
        print("🔧 ENDPOINTS CASSÉS (Priorité 1 - À corriger immédiatement)")
        print("-" * 60)
        for url, status, err, sugg, endpoint in build_errors:
            print(f"[{status}] {url} (endpoint: {endpoint})")
            if sugg:
                print(f"   {sugg}")
            print()
    
    if jinja_errors:
        print("🏷️ VARIABLES JINJA2 MANQUANTES (Priorité 2)")
        print("-" * 60)
        for url, status, err, sugg, endpoint in jinja_errors:
            print(f"[{status}] {url} (endpoint: {endpoint})")
            if sugg:
                print(f"   {sugg}")
            print()
    
    if other_errors:
        print("❌ AUTRES ERREURS (Priorité 3)")
        print("-" * 60)
        for url, status, err, sugg, endpoint in other_errors:
            print(f"[{status}] {url} (endpoint: {endpoint})")
            if sugg:
                print(f"   {sugg}")
            else:
                print(f"   Erreur: {err[:200]}...")
            print()

def main():
    print("🚀 Démarrage du test des endpoints Fée Maison...")
    
    build_errors, jinja_errors, other_errors = test_all_routes(app)
    
    if not any([build_errors, jinja_errors, other_errors]):
        print("✅ Aucune erreur détectée sur les endpoints accessibles en GET.")
        print("🎉 Votre application Fée Maison semble en bonne santé !")
    else:
        print_errors_by_category(build_errors, jinja_errors, other_errors)
        
        # Actions prioritaires
        if build_errors:
            print("🚨 ACTIONS PRIORITAIRES:")
            print("1. Corrige les endpoints cassés dans tes templates (base.html, etc.)")
            print("2. Vérifie que tous les blueprints sont bien enregistrés")
            print("3. Redémarre l'application après corrections")

if __name__ == "__main__":
    main()
