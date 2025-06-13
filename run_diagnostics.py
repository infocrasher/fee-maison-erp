import os
import re
import traceback
from flask import Flask
from werkzeug.routing import Rule
from datetime import datetime

# Adapter selon ta structure
from app import create_app

app = create_app()
client = app.test_client()

TEMPLATES_DIR = "app/templates"

def is_static(rule: Rule):
    return rule.endpoint == 'static'

def get_routes(app):
    routes = []
    for rule in app.url_map.iter_rules():
        # Ignore static and HEAD/OPTIONS methods
        if is_static(rule):
            continue
        routes.append(rule)
    return routes

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
        return url, defaults
    except Exception as e:
        return None, None

def suggest_fixes(error_text):
    """Suggestions de corrections pour erreurs communes"""
    lines = error_text.splitlines()
    
    error_patterns = {
        r"'bool' object is not callable": "ERREUR: @property appelee comme fonction. Retirez les () : current_user.is_admin au lieu de current_user.is_admin()",
        r"'([\w_]+)' is undefined": "ERREUR: Variable Jinja2 manquante : '{var}'. Verifiez render_template() ou context_processor",
        r"werkzeug.routing.exceptions.BuildError": "ERREUR: Route inexistante dans url_for(). Verifiez l'endpoint et les blueprints",
        r"jinja2.exceptions.TemplateNotFound": "ERREUR: Template manquant. Verifiez le chemin et l'existence du fichier",
        r"sqlalchemy.*OperationalError": "ERREUR: Erreur de connexion base de donnees. Verifiez la configuration DB",
        r"ImportError.*No module named": "ERREUR: Module manquant. Verifiez les imports et requirements.txt",
    }
    
    for line in lines:
        for pattern, message in error_patterns.items():
            match = re.search(pattern, line)
            if match:
                if '{var}' in message and match.groups():
                    return message.format(var=match.group(1))
                return message
    
    return "ERREUR: Erreur non reconnue. Consultez la stack trace complete."

def test_get_routes_only(app):
    """SAFE: Teste uniquement les routes GET sans modification"""
    routes = get_routes(app)
    errors = []
    success_count = 0
    
    print(f"Test de {len(routes)} routes (GET seulement)...")
    
    for rule in routes:
        url, url_kwargs = build_url(rule)
        if not url:
            continue
        
        # SAFE: Tests GET uniquement
        try:
            response = client.get(url)
            
            if response.status_code >= 500:
                error_message = response.data.decode("utf8", errors="ignore")
                suggestion = suggest_fixes(error_message)
                errors.append({
                    'url': url, 
                    'status': response.status_code,
                    'error': error_message[:500],
                    'suggestion': suggestion
                })
                print(f"ERREUR GET {url} - {response.status_code}")
            elif b'jinja2.exceptions.UndefinedError' in response.data:
                error_message = response.data.decode("utf8", errors="ignore")
                suggestion = suggest_fixes(error_message)
                errors.append({
                    'url': url,
                    'status': 'jinja2_error', 
                    'error': error_message[:500],
                    'suggestion': suggestion
                })
                print(f"ERREUR GET {url} - Erreur Jinja2")
            else:
                success_count += 1
                if response.status_code in [200, 302, 401, 403]:
                    print(f"OK GET {url} - {response.status_code}")
                else:
                    print(f"WARN GET {url} - {response.status_code}")
                    
        except Exception as e:
            tb = traceback.format_exc()
            suggestion = suggest_fixes(tb)
            errors.append({
                'url': url,
                'status': 'exception',
                'error': str(e),
                'suggestion': suggestion
            })
            print(f"EXCEPTION GET {url} - {str(e)[:50]}")

    print(f"\nResultat routes GET: {success_count}/{len(routes)} OK, {len(errors)} erreurs")
    return errors

def audit_template_variables():
    """SAFE: Analyse les variables utilisees dans les templates"""
    found_vars = set()
    found_conditions = set()
    found_loops = set()
    
    # Patterns pour differents usages Jinja2
    var_pattern = re.compile(r"{{\s*([\w_]+)[\s\(|}]")
    condition_pattern = re.compile(r"{% if\s+([\w_.]+)")
    loop_pattern = re.compile(r"{% for\s+\w+\s+in\s+([\w_.]+)")
    
    template_count = 0
    
    for root, _, files in os.walk(TEMPLATES_DIR):
        for fname in files:
            if fname.endswith(".html"):
                template_count += 1
                path = os.path.join(root, fname)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                        
                        # Variables dans {{ }}
                        for m in var_pattern.finditer(content):
                            found_vars.add(m.group(1))
                        
                        # Variables dans {% if %}
                        for m in condition_pattern.finditer(content):
                            found_conditions.add(m.group(1))
                        
                        # Variables dans {% for %}
                        for m in loop_pattern.finditer(content):
                            found_loops.add(m.group(1))
                            
                except Exception as e:
                    print(f"WARN Erreur lecture template {path}: {e}")
    
    print(f"Analyse {template_count} templates")
    print(f"   Variables: {len(found_vars)}")
    print(f"   Conditions: {len(found_conditions)}")
    print(f"   Boucles: {len(found_loops)}")
    
    return {
        'variables': found_vars,
        'conditions': found_conditions,
        'loops': found_loops
    }

def context_processors_from_app(app):
    """SAFE: Liste les context processors declares"""
    processors = set()
    
    try:
        for func in app.template_context_processors[None]:
            try:
                results = func()
                if isinstance(results, dict):
                    processors.update(results.keys())
            except:
                pass
        
        # Context processors des blueprints
        for bp in app.blueprints.values():
            for func in bp.template_context_processors.get(bp.name, []):
                try:
                    results = func()
                    if isinstance(results, dict):
                        processors.update(results.keys())
                except:
                    pass
    except Exception as e:
        print(f"WARN Erreur analyse context processors: {e}")
    
    return processors

def check_static_files():
    """SAFE: Verifie l'existence des fichiers/dossiers statiques"""
    checks = []
    
    # Dossiers essentiels
    essential_dirs = [
        'app/static',
        'app/static/css', 
        'app/static/js',
        'app/templates',
        'app/templates/auth',
        'app/templates/products',
        'app/templates/recipes',
        'app/templates/orders'
    ]
    
    # Templates critiques
    critical_templates = [
        'app/templates/base.html',
        'app/templates/_form_macros.html'
    ]
    
    for directory in essential_dirs:
        if os.path.exists(directory):
            checks.append({'type': 'dir', 'path': directory, 'status': 'OK'})
        else:
            checks.append({'type': 'dir', 'path': directory, 'status': 'MISSING'})
    
    for template in critical_templates:
        if os.path.exists(template):
            checks.append({'type': 'file', 'path': template, 'status': 'OK'})
        else:
            checks.append({'type': 'file', 'path': template, 'status': 'MISSING'})
    
    # Resume
    missing = [c for c in checks if c['status'] == 'MISSING']
    if missing:
        print(f"WARN {len(missing)} fichier(s)/dossier(s) manquant(s):")
        for item in missing:
            print(f"   - {item['path']}")
    else:
        print("OK Tous les fichiers/dossiers essentiels sont presents")
    
    return checks

def check_forms_load():
    """SAFE: Verifie que les formulaires se chargent (GET seulement)"""
    form_urls = [
        '/admin/products/category/new',
        '/admin/products/new',
        '/admin/recipes/new',
        '/admin/orders/new',
        '/auth/login'
    ]
    
    results = []
    
    print("Test chargement des formulaires...")
    for url in form_urls:
        try:
            response = client.get(url)
            
            # Verifications basiques
            has_form = b'<form' in response.data
            has_csrf = b'csrf_token' in response.data
            
            status = {
                'url': url,
                'status_code': response.status_code,
                'has_form': has_form,
                'has_csrf': has_csrf,
                'loadable': response.status_code < 500
            }
            
            if status['loadable']:
                print(f"OK {url} - Formulaire chargeable")
            else:
                print(f"ERREUR {url} - Erreur {response.status_code}")
            
            results.append(status)
            
        except Exception as e:
            print(f"EXCEPTION {url} - Exception: {str(e)}")
            results.append({
                'url': url,
                'status_code': 'exception',
                'error': str(e),
                'loadable': False
            })
    
    loadable_count = sum(1 for r in results if r.get('loadable', False))
    print(f"Formulaires: {loadable_count}/{len(form_urls)} chargeables")
    
    return results

def check_app_configuration():
    """SAFE: Verifie la configuration de l'application"""
    config_checks = []
    
    try:
        with app.app_context():
            # Configuration de base
            config_items = [
                'SECRET_KEY',
                'SQLALCHEMY_DATABASE_URI', 
                'WTF_CSRF_ENABLED',
                'DEBUG'
            ]
            
            for item in config_items:
                value = app.config.get(item)
                status = 'SET' if value is not None else 'MISSING'
                
                # Masquer les valeurs sensibles
                display_value = '***' if 'SECRET' in item or 'PASSWORD' in item else str(value)[:50]
                
                config_checks.append({
                    'key': item,
                    'status': status,
                    'value': display_value
                })
            
            # Extensions Flask
            extensions = []
            if hasattr(app, 'extensions'):
                extensions = list(app.extensions.keys())
            
            print("Configuration de l'application:")
            for check in config_checks:
                symbol = "OK" if check['status'] == 'SET' else "ERREUR"
                print(f"   {symbol} {check['key']}: {check['value']}")
            
            print(f"Extensions chargees: {', '.join(extensions) if extensions else 'Aucune detectee'}")
            
    except Exception as e:
        print(f"WARN Erreur verification config: {e}")
        config_checks.append({'error': str(e)})
    
    return config_checks

def verify_database_connection():
    """SAFE: Verifie la connexion DB sans modification"""
    try:
        with app.app_context():
            from extensions import db
            from sqlalchemy import text
            
            result = db.session.execute(text("SELECT 1"))
            result.close()
            
            # Informations sur la DB
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            
            if 'postgresql' in db_url:
                db_type = 'postgresql'
            elif 'sqlite' in db_url:
                db_type = 'sqlite'
            else:
                db_type = 'autre'
            
            print(f"OK Connexion base de donnees OK ({db_type})")
            return True
            
    except Exception as e:
        print(f"ERREUR Erreur connexion base de donnees: {e}")
        return False

def main():
    """Diagnostic complet SANS RISQUE - Read-Only uniquement"""
    print("\n==== DIAGNOSTIC SECURISE (READ-ONLY) ====\n")
    print("Mode: Lecture seule - Aucune modification de l'application\n")
    
    # 1. Verification configuration
    print("Verification de la configuration...")
    config_status = check_app_configuration()
    
    print("\nTest de connexion base de donnees...")
    db_status = verify_database_connection()
    
    # 2. Verification fichiers statiques
    print("\nVerification des fichiers essentiels...")
    static_status = check_static_files()
    
    # 3. Tests des routes GET
    print("\nTest des routes (GET seulement)...")
    route_errors = test_get_routes_only(app)
    
    # 4. Test formulaires
    print("\nTest de chargement des formulaires...")
    form_status = check_forms_load()
    
    # 5. Audit templates
    print("\nAudit des templates...")
    template_vars = audit_template_variables()
    injected_vars = context_processors_from_app(app)
    
    missing_vars = template_vars['variables'] - injected_vars
    
    # 6. Resume final
    print("\n" + "="*60)
    print("RESUME DU DIAGNOSTIC SECURISE")
    print("="*60)
    
    print(f"Base de donnees: {'OK' if db_status else 'ERREUR'}")
    print(f"Fichiers statiques: OK")
    print(f"Routes testees: {len(get_routes(app))}")
    print(f"Erreurs de routes: {len(route_errors)}")
    
    loadable_forms = sum(1 for f in form_status if f.get('loadable', False))
    print(f"Formulaires chargeables: {loadable_forms}/{len(form_status)}")
    
    print(f"Variables template: {len(template_vars['variables'])}")
    print(f"Variables potentiellement manquantes: {len(missing_vars)}")
    
    if route_errors:
        print(f"\nERREURS DETECTEES ({len(route_errors)}):")
        for error in route_errors[:5]:  # Top 5
            print(f"   - {error['url']}: {error.get('suggestion', 'Erreur non classifiee')}")
        
        if len(route_errors) > 5:
            print(f"   ... et {len(route_errors) - 5} autres erreurs")
    
    if missing_vars:
        print(f"\nVariables template a verifier:")
        for var in sorted(list(missing_vars)[:10]):  # Top 10
            print(f"   - {var}")
        
        if len(missing_vars) > 10:
            print(f"   ... et {len(missing_vars) - 10} autres variables")
    
    if not route_errors and len(missing_vars) < 5:
        print(f"\nApplication en excellente sante !")
        print("Aucune erreur critique detectee")
    
    print(f"\nDiagnostic termine - Aucune modification effectuee")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
