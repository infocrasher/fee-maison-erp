import os
import re
from flask import Flask
from werkzeug.routing import Rule
from jinja2 import Environment, FileSystemLoader
import traceback

# Adapter selon ta structure
from app import create_app

app = create_app()
client = app.test_client()

def is_static(rule: Rule):
    return rule.endpoint == 'static'

def get_routes(app):
    routes = []
    for rule in app.url_map.iter_rules():
        if is_static(rule):
            continue
        if 'GET' in rule.methods:
            routes.append(rule)
    return routes

def get_all_endpoints(app):
    return set(app.view_functions.keys())

def build_url(rule):
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

def find_url_for_calls(template_folder):
    """Trouve tous les appels url_for dans les templates HTML"""
    url_for_calls = set()
    
    if not os.path.exists(template_folder):
        print(f"❌ Dossier templates non trouvé : {template_folder}")
        return url_for_calls
    
    html_files_found = 0
    for dirpath, _, filenames in os.walk(template_folder):
        for fname in filenames:
            if fname.endswith('.html'):
                html_files_found += 1
                file_path = os.path.join(dirpath, fname)
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
                        # Patterns pour url_for
                        patterns = [
                            r"url_for\(['\"]([\w\.]+)['\"]",      # url_for('endpoint')
                            r"url_for\(\"([\w\.]+)\"",           # url_for("endpoint")
                            r"url_for\('([\w\.]+)'",             # url_for('endpoint')
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            url_for_calls.update(matches)
                            
                except Exception as e:
                    print(f"⚠️ Erreur lecture {file_path}: {e}")
    
    print(f"📄 {html_files_found} fichiers HTML analysés dans {template_folder}")
    return url_for_calls

def get_expected_endpoints():
    """Endpoints qu'on s'attend à trouver dans Fée Maison"""
    return {
        # Navigation principale
        'main.dashboard', 'main.hello_world',
        'auth.login', 'auth.logout', 'auth.account',
        
        # Gestion produits
        'products.list_categories', 'products.new_category', 'products.edit_category',
        'products.list_products', 'products.new_product', 'products.edit_product', 'products.view_product',
        
        # Commandes - nouvelles routes
        'orders.new_customer_order', 'orders.new_production_order',
        'orders.list_customer_orders', 'orders.list_production_orders',
        'orders.list_orders', 'orders.new_order', 'orders.view_order', 'orders.edit_order',
        'orders.edit_order_status', 'orders.orders_calendar',
        
        # Recettes
        'recipes.list_recipes', 'recipes.new_recipe', 'recipes.edit_recipe', 'recipes.view_recipe',
        
        # Stock
        'stock.overview', 'stock.quick_entry', 'stock.adjustment',
        
        # Admin
        'admin.dashboard'
    }

def check_template_endpoints(template_folder, app):
    print("🔎 Analyse des endpoints utilisés dans les templates HTML...")
    
    # Debug du chemin
    abs_path = os.path.abspath(template_folder)
    print(f"📁 Chemin templates : {abs_path}")
    print(f"📁 Dossier existe : {os.path.exists(template_folder)}")
    
    if os.path.exists(template_folder):
        html_files = []
        for root, dirs, files in os.walk(template_folder):
            for file in files:
                if file.endswith('.html'):
                    html_files.append(os.path.join(root, file))
        
        print(f"📄 Fichiers HTML trouvés : {len(html_files)}")
        for f in html_files[:3]:  # Afficher les 3 premiers
            rel_path = os.path.relpath(f, template_folder)
            print(f"   - {rel_path}")
        if len(html_files) > 3:
            print(f"   ... et {len(html_files) - 3} autres")
    
    # Analyse des endpoints
    template_endpoints = find_url_for_calls(template_folder)
    real_endpoints = get_all_endpoints(app)
    expected_endpoints = get_expected_endpoints()
    
    print(f"\n📊 Statistiques :")
    print(f"   - Endpoints trouvés dans templates : {len(template_endpoints)}")
    print(f"   - Endpoints réels dans l'app : {len(real_endpoints)}")
    print(f"   - Endpoints attendus : {len(expected_endpoints)}")
    
    # Endpoints cassés (utilisés mais inexistants)
    missing = template_endpoints - real_endpoints
    if missing:
        print(f"\n❌ {len(missing)} endpoints utilisés dans les templates mais non déclarés dans l'app :")
        for ep in sorted(missing):
            print(f"   - {ep}")
    else:
        print(f"\n✅ Tous les endpoints utilisés dans les templates existent bien dans l'app.")
    
    # Endpoints trouvés dans les templates
    if template_endpoints:
        print(f"\n🔍 Endpoints trouvés dans les templates :")
        for ep in sorted(template_endpoints):
            status = "✅" if ep in real_endpoints else "❌"
            print(f"   {status} {ep}")
    
    # Endpoints attendus mais non trouvés dans les templates
    expected_missing = expected_endpoints - template_endpoints
    if expected_missing:
        print(f"\n⚠️ {len(expected_missing)} endpoints attendus mais non trouvés dans les templates :")
        for ep in sorted(expected_missing):
            if ep in real_endpoints:
                print(f"   - {ep} (existe dans l'app)")
    
    # Endpoints orphelins (déclarés mais jamais utilisés)
    orphan = real_endpoints - template_endpoints
    if orphan:
        significant_orphan = [ep for ep in orphan if not ep.startswith('_') and ep != "static" and "delete" not in ep]
        if significant_orphan:
            print(f"\n⚠️ {len(significant_orphan)} endpoints Flask déclarés mais jamais utilisés dans les templates :")
            for ep in sorted(significant_orphan):
                print(f"   - {ep}")
    
    print()

def suggest_fixes(error_text, endpoint):
    """Suggestions de corrections pour les erreurs[1]"""
    endpoint_fixes = {
        'categories.list_categories': 'products.list_categories',
        'categories.new_category': 'products.new_category',
        'categories.edit_category': 'products.edit_category',
        'stock.list_stock': 'stock.overview',
        'stock.stock_overview': 'stock.overview',
        'main.home': 'main.dashboard',
    }
    
    # BuildError
    if "werkzeug.routing.exceptions.BuildError" in error_text:
        build_error_match = re.search(r"Could not build url for endpoint '([^']+)'", error_text)
        if build_error_match:
            broken_endpoint = build_error_match.group(1)
            if broken_endpoint in endpoint_fixes:
                return f"🔧 CORRECTION : '{broken_endpoint}' → '{endpoint_fixes[broken_endpoint]}'"
            else:
                return f"🔧 Endpoint manquant : '{broken_endpoint}' - Vérifiez qu'il existe dans les routes"
        return "❗ BuildError - Endpoint non trouvé"
    
    # UndefinedError
    if 'jinja2.exceptions.UndefinedError' in error_text:
        var_match = re.search(r"'([\w_]+)' is undefined", error_text)
        if var_match:
            var = var_match.group(1)
            common_fixes = {
                'render_field': "Importez la macro render_field dans le template",
                'title': "Passez 'title' dans render_template()",
                'form': "Passez 'form' dans render_template()",
                'current_user': "Vérifiez Flask-Login",
                'get_flashed_messages': "Importez get_flashed_messages",
            }
            if var in common_fixes:
                return f"🏷️ Variable manquante : '{var}' - {common_fixes[var]}"
            else:
                return f"🏷️ Variable Jinja2 manquante : '{var}'"
    
    return "❓ Erreur inconnue"

def test_all_routes(app):
    routes = get_routes(app)
    errors = []
    success_count = 0
    
    print(f"🔍 Test de {len(routes)} routes GET...")
    
    for rule in routes:
        url = build_url(rule)
        if not url:
            continue
        
        try:
            response = client.get(url)
            
            # Check for errors
            is_error = False
            error_msg = ""
            
            if response.status_code >= 500:
                is_error = True
                error_msg = response.data.decode("utf8", errors="ignore")
            elif b'jinja2.exceptions.UndefinedError' in response.data:
                is_error = True
                error_msg = response.data.decode("utf8", errors="ignore")
            elif b'werkzeug.routing.exceptions.BuildError' in response.data:
                is_error = True
                error_msg = response.data.decode("utf8", errors="ignore")
            
            if is_error:
                suggestion = suggest_fixes(error_msg, rule.endpoint)
                print(f"❌ [{response.status_code}] {url}")
                print(f"   Endpoint: {rule.endpoint}")
                print(f"   {suggestion}")
                
                # Afficher un extrait de l'erreur
                error_lines = error_msg.split('\n')
                key_lines = [line for line in error_lines if any(keyword in line for keyword in ['BuildError', 'UndefinedError', 'File '])][:3]
                if key_lines:
                    print(f"   Détail: {key_lines[0][:100]}...")
                print()
                errors.append((url, response.status_code, error_msg, suggestion, rule.endpoint))
            else:
                success_count += 1
                
        except Exception as e:
            tb = traceback.format_exc()
            suggestion = suggest_fixes(tb, rule.endpoint)
            print(f"❌ EXCEPTION {url}")
            print(f"   Endpoint: {rule.endpoint}")
            print(f"   {suggestion}")
            print(f"   Erreur: {str(e)[:100]}...")
            print()
            errors.append((url, 'EXCEPTION', tb, suggestion, rule.endpoint))
    
    print(f"📊 Résultat : {success_count}/{len(routes)} routes OK, {len(errors)} erreurs")
    return errors

def find_correct_template_path():
    """Trouve automatiquement le bon chemin vers les templates"""
    possible_paths = [
        'app/templates',
        'templates',
        '../app/templates',
        './app/templates',
        os.path.join(os.path.dirname(__file__), 'app/templates'),
        os.path.join(os.path.dirname(__file__), '../app/templates'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            html_count = 0
            for root, dirs, files in os.walk(path):
                html_count += len([f for f in files if f.endswith('.html')])
            
            if html_count > 0:
                print(f"✅ Templates trouvés : {path} ({html_count} fichiers HTML)")
                return path
    
    print("❌ Aucun dossier templates trouvé")
    return None

def main():
    print("🚀 Vérification automatique des endpoints Flask et des templates Jinja2")
    print("=" * 80)
    
    # 1. Test runtime sur tous les endpoints GET
    print("\n📋 PHASE 1 : Test des routes en temps réel")
    errors = test_all_routes(app)
    
    # 2. Analyse statique : endpoints utilisés vs déclarés
    print("\n📋 PHASE 2 : Analyse statique des templates")
    templates_folder = find_correct_template_path()
    
    if templates_folder:
        check_template_endpoints(templates_folder, app)
    else:
        print("⚠️ Impossible d'analyser les templates - dossier non trouvé")
    
    # 3. Résumé final
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    
    if not errors:
        print("🎉 Excellent ! Aucune erreur détectée sur les routes GET.")
        print("✅ Votre application Fée Maison semble en parfait état !")
    else:
        print(f"⚠️ {len(errors)} erreurs détectées nécessitent votre attention.")
        print("🔧 Priorité : Corrigez les BuildError en premier (endpoints cassés)")
        print("🏷️ Ensuite : Vérifiez les variables Jinja2 manquantes")
    
    print(f"\n📈 Statistiques globales :")
    print(f"   - Routes testées : {len(get_routes(app))}")
    print(f"   - Endpoints déclarés : {len(get_all_endpoints(app))}")
    print(f"   - Templates analysés : {templates_folder or 'Non trouvé'}")
    
    print("\n✅ Analyse terminée.")

if __name__ == "__main__":
    main()
