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
    env = Environment(loader=FileSystemLoader(template_folder))
    url_for_calls = set()
    for dirpath, _, filenames in os.walk(template_folder):
        for fname in filenames:
            if fname.endswith('.html'):
                try:
                    with open(os.path.join(dirpath, fname), encoding='utf-8') as f:
                        content = f.read()
                        matches = re.findall(r"url_for\(['\"]([\w\.]+)['\"]", content)
                        url_for_calls.update(matches)
                except Exception:
                    pass
    return url_for_calls

def check_template_endpoints(template_folder, app):
    print("🔎 Analyse des endpoints utilisés dans les templates HTML...")
    template_endpoints = find_url_for_calls(template_folder)
    real_endpoints = get_all_endpoints(app)
    missing = template_endpoints - real_endpoints
    orphan = real_endpoints - template_endpoints
    if missing:
        print("❌ Endpoints utilisés dans les templates mais non déclarés dans l'app :")
        for ep in sorted(missing):
            print(f"   - {ep}")
    else:
        print("✅ Tous les endpoints utilisés dans les templates existent bien dans l'app.")
    print()
    if orphan:
        print("⚠️ Endpoints Flask déclarés mais jamais utilisés dans les templates :")
        for ep in sorted(orphan):
            if not ep.startswith('_') and ep != "static":
                print(f"   - {ep}")
    else:
        print("✅ Tous les endpoints déclarés sont utilisés dans au moins un template.")
    print()

def test_all_routes(app):
    routes = get_routes(app)
    errors = []
    print(f"🔍 Test de {len(routes)} routes GET...")
    for rule in routes:
        url = build_url(rule)
        if not url:
            continue
        try:
            response = client.get(url)
            if response.status_code >= 500 or b'jinja2.exceptions.UndefinedError' in response.data or b'werkzeug.routing.exceptions.BuildError' in response.data:
                error_message = response.data.decode("utf8", errors="ignore")
                print(f"❌ [{response.status_code}] {url} (endpoint: {rule.endpoint})")
                print(f"---\n{error_message[:500]}\n---\n")
        except Exception:
            tb = traceback.format_exc()
            print(f"❌ Exception lors du test de l'URL {url} (endpoint: {rule.endpoint})\n{tb}\n")

def main():
    print("🚀 Vérification automatique des endpoints Flask et des templates Jinja2")
    # 1. Test runtime sur tous les endpoints GET
    test_all_routes(app)
    # 2. Analyse statique : endpoints utilisés vs déclarés
    templates_folder = os.path.join(os.path.dirname(__file__), '../templates')
    check_template_endpoints(templates_folder, app)
    print("✅ Analyse terminée.")

if __name__ == "__main__":
    main()