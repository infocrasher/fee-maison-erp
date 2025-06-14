import traceback
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

def suggest_fixes(error_text):
    lines = error_text.splitlines()
    for line in lines:
        # Suggestion pour variable Jinja2 non définie
        if 'jinja2.exceptions.UndefinedError' in line:
            # Extrait le nom de la variable manquante
            import re
            m = re.search(r"'([\w_]+)' is undefined", line)
            if m:
                var = m.group(1)
                return f"❗ Variable Jinja2 manquante : '{var}'.\n   ➔ Vérifie que tu passes bien '{var}' dans le render_template OU que tu as bien importé le contexte global (ex. pour CSRF, forms etc)."
            else:
                return f"❗ Variable Jinja2 non définie détectée. Vérifie le contexte passé au template."
        if "werkzeug.routing.exceptions.BuildError" in line:
            return "❗ Endpoint Flask non trouvé (BuildError). Vérifie le nom de l'endpoint dans url_for et la déclaration de ta route."
    return ""

def test_all_routes(app):
    routes = get_routes(app)
    errors = []
    for rule in routes:
        url = build_url(rule)
        if not url:
            continue
        try:
            response = client.get(url)
            # On cherche des erreurs dans la réponse
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
                errors.append((url, response.status_code, error_message, suggestion))
        except Exception as e:
            tb = traceback.format_exc()
            suggestion = suggest_fixes(tb)
            errors.append((url, 'EXCEPTION', tb, suggestion))
    return errors

def main():
    errors = test_all_routes(app)
    print("\n==== Rapport des erreurs détectées ====\n")
    if not errors:
        print("✅ Aucune erreur détectée sur les endpoints accessibles en GET.")
    else:
        for url, status, err, sugg in errors:
            print(f"[{status}] {url}\n{'-'*50}\n{err.strip()}\n")
            if sugg:
                print(f"Suggestion :\n{sugg}\n")
            print("="*80)

if __name__ == "__main__":
    main()