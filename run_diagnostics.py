import os
import re
import traceback
from flask import Flask
from werkzeug.routing import Rule

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
    lines = error_text.splitlines()
    for line in lines:
        # Suggestion pour variable Jinja2 non définie
        if 'jinja2.exceptions.UndefinedError' in line:
            import re
            m = re.search(r"'([\w_]+)' is undefined", line)
            if m:
                var = m.group(1)
                return f"❗ Variable Jinja2 manquante : '{var}'.\n   ➔ Vérifie que tu passes bien '{var}' dans le render_template OU que tu as bien un context processor qui l'injecte."
            else:
                return f"❗ Variable Jinja2 non définie détectée. Vérifie le contexte passé au template."
        if "werkzeug.routing.exceptions.BuildError" in line:
            return "❗ Endpoint Flask non trouvé (BuildError). Vérifie le nom de l'endpoint dans url_for et la déclaration de ta route."
    return None

def audit_templates_vars():
    """Liste toutes les variables/fonctions utilisées dans les templates."""
    found = set()
    var_pattern = re.compile(r"{{\s*([\w_]+)[\s\(|}]")  # attrape {{ variable }} ou {{ fonction( }}
    for root, _, files in os.walk(TEMPLATES_DIR):
        for fname in files:
            if fname.endswith(".html"):
                path = os.path.join(root, fname)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    for m in var_pattern.finditer(content):
                        found.add(m.group(1))
    return found

def context_processors_from_app(app):
    """Liste tous les context processors déclarés."""
    processors = set()
    for func in app.template_context_processors[None]:
        results = func()
        if isinstance(results, dict):
            processors.update(results.keys())
    # On peut aussi parser les blueprints si besoin
    for bp in app.blueprints.values():
        for func in bp.template_context_processors.get(bp.name, []):
            results = func()
            if isinstance(results, dict):
                processors.update(results.keys())
    return processors

def test_all_routes(app):
    routes = get_routes(app)
    errors = []
    for rule in routes:
        url, url_kwargs = build_url(rule)
        if not url:
            continue
        # GET
        try:
            response = client.get(url)
            error_found = False
            error_message = ""
            if response.status_code >= 500:
                error_found = True
                error_message = response.data.decode("utf8", errors="ignore")
            elif b'jinja2.exceptions.UndefinedError' in response.data:
                error_found = True
                error_message = response.data.decode("utf8", errors="ignore")
            if error_found:
                suggestion = suggest_fixes(error_message)
                errors.append({
                    'url': url, 'method': 'GET', 'status': response.status_code,
                    'error': error_message, 'suggestion': suggestion})
        except Exception as e:
            tb = traceback.format_exc()
            suggestion = suggest_fixes(tb)
            errors.append({'url': url, 'method': 'GET', 'status': 'EXCEPTION',
                           'error': tb, 'suggestion': suggestion})

        # POST (tentative naïve)
        try:
            # On ne sait pas ce qu'il faut poster, alors on envoie des champs fictifs
            form = {k: v for k, v in url_kwargs.items()}
            # Ajoute des champs classiques
            form.update({"dummy": "test", "csrf_token": "fake"})
            response = client.post(url, data=form, follow_redirects=True)
            if response.status_code >= 500 or b'jinja2.exceptions.UndefinedError' in response.data:
                error_message = response.data.decode("utf8", errors="ignore")
                suggestion = suggest_fixes(error_message)
                errors.append({
                    'url': url, 'method': 'POST', 'status': response.status_code,
                    'error': error_message, 'suggestion': suggestion})
        except Exception as e:
            tb = traceback.format_exc()
            suggestion = suggest_fixes(tb)
            errors.append({'url': url, 'method': 'POST', 'status': 'EXCEPTION',
                           'error': tb, 'suggestion': suggestion})

    return errors

def main():
    print("\n==== SUPER DIAGNOSTIC FLASK/JINJA2 ====\n")
    # 1. Test routes
    errors = test_all_routes(app)
    if errors:
        print("\n---- Résumé des erreurs détectées ----\n")
        for err in errors:
            print(f"[{err['status']}] {err['method']} {err['url']}\n{'-'*50}\n{err['error']}\n")
            if err['suggestion']:
                print(f"Suggestion :\n{err['suggestion']}\n")
            print("="*80)
    else:
        print("✅ Aucune erreur 500/Jinja2 détectée sur les endpoints GET et POST.\n")

    # 2. Audit variables/fonctions Jinja2 vs context processors
    print("\n==== AUDIT JINJA2 : Variables utilisées vs injectées ====\n")
    used_vars = audit_templates_vars()
    injected_vars = context_processors_from_app(app)
    missing = used_vars - injected_vars
    print("Variables/fonctions utilisées dans les templates mais pas injectées globalement :")
    for var in sorted(missing):
        print("-", var)
    if "csrf_token" in missing:
        print("⚠️  'csrf_token' est souvent injecté par Flask-WTF. Vérifie que le context_processor est bien activé.")
    print("\n\n==== FIN DU RAPPORT ====\n")

if __name__ == "__main__":
    main()