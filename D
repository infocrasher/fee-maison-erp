import os
import re
import importlib
import inspect
from flask import Flask

# === À personnaliser : résumé métier et roadmap ===

SUMMARY = """
### 🏪 Nature de l'Activité

"Fée Maison" est une entreprise de production et vente de produits alimentaires artisanaux opérant sur deux sites :
- Magasin principal : Vente au comptoir et prise de commandes
- Local de production : Fabrication des produits (200m du magasin)
...
"""

ROADMAP = """
## 🚩 Roadmap ERP Fée Maison

✅ PHASE 1 : FOUNDATION (TERMINÉE)
🏗️ Infrastructure de Base
...
TOTAL RESTANT : 25-33 semaines (6-8 mois)

🏆 Objectif Final
ERP complet et autonome pour Fée Maison avec toutes les fonctionnalités métier, hébergé localement avec accès web via nom de domaine, formation complète des utilisatrices et documentation exhaustive.
"""

# === Paramètres projet ===
APP_IMPORT_STRING = "app:create_app"  # Adapter si besoin
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "app", "templates")
MODELS_DIR = os.path.join(PROJECT_ROOT, "app", "models")
FORMS_DIR = os.path.join(PROJECT_ROOT, "app", "forms")

def scan_project_structure(base_path, max_depth=5):
    tree = []
    for dirpath, dirnames, filenames in os.walk(base_path):
        rel_path = os.path.relpath(dirpath, base_path)
        depth = rel_path.count(os.sep)
        if depth > max_depth:
            continue
        indent = "  " * depth
        tree.append(f"{indent}- {os.path.basename(dirpath)}/")
        for f in filenames:
            tree.append(f"{indent}  - {f}")
    return "\n".join(tree)

def extract_flask_routes(app):
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        view_func = app.view_functions[rule.endpoint]
        doc = inspect.getdoc(view_func) or ""
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        routes.append({
            "rule": rule.rule,
            "endpoint": rule.endpoint,
            "methods": methods,
            "doc": doc,
            "blueprint": rule.endpoint.split('.')[0] if '.' in rule.endpoint else ''
        })
    return routes

def extract_models_info():
    result = []
    if not os.path.isdir(MODELS_DIR):
        return result
    for fname in os.listdir(MODELS_DIR):
        if fname.endswith(".py") and not fname.startswith("__"):
            modname = f"app.models.{fname[:-3]}"
            try:
                mod = importlib.import_module(modname)
                for name, cls in inspect.getmembers(mod, inspect.isclass):
                    if hasattr(cls, "__tablename__"):
                        fields = []
                        for attr in dir(cls):
                            if attr.startswith("_"): continue
                            val = getattr(cls, attr)
                            if hasattr(val, "property"):
                                col = getattr(val.property, "columns", None)
                                if col:
                                    fields.append(f"{attr}: {str(col[0].type)}")
                        result.append({
                            "model": name,
                            "fields": fields,
                            "file": fname
                        })
            except Exception as e:
                result.append({"model": fname, "fields": [f"Erreur: {e}"], "file": fname})
    return result

def extract_forms_info():
    forms = []
    if not os.path.isdir(FORMS_DIR):
        return forms
    for fname in os.listdir(FORMS_DIR):
        if fname.endswith(".py") and not fname.startswith("__"):
            modname = f"app.forms.{fname[:-3]}"
            try:
                mod = importlib.import_module(modname)
                for name, cls in inspect.getmembers(mod, inspect.isclass):
                    if "Form" in name:
                        fields = []
                        for attr in dir(cls):
                            if not attr.startswith("_") and not callable(getattr(cls, attr)) and not attr.isupper():
                                fields.append(attr)
                        forms.append({"form": name, "fields": fields, "file": fname})
            except Exception as e:
                forms.append({"form": fname, "fields": [f"Erreur: {e}"], "file": fname})
    return forms

def extract_context_processors(app):
    ctx_vars = set()
    for func in app.template_context_processors[None]:
        try:
            res = func()
            if isinstance(res, dict):
                ctx_vars.update(res.keys())
        except Exception:
            pass
    for bp in app.blueprints.values():
        for func in bp.template_context_processors.get(bp.name, []):
            try:
                res = func()
                if isinstance(res, dict):
                    ctx_vars.update(res.keys())
            except Exception:
                pass
    return sorted(ctx_vars)

def extract_jinja_vars_macros(templates_dir):
    found_vars = set()
    found_macros = set()
    var_pattern = re.compile(r"{{\s*([\w_]+)[\s\(|}]")
    macro_pattern = re.compile(r"{% macro ([\w_]+)\(")
    for root, _, files in os.walk(templates_dir):
        for fname in files:
            if fname.endswith(".html"):
                path = os.path.join(root, fname)
                try:
                    content = open(path, encoding="utf-8").read()
                    found_vars.update(var_pattern.findall(content))
                    found_macros.update(macro_pattern.findall(content))
                except Exception:
                    pass
    return sorted(found_vars), sorted(found_macros)

def main():
    # Import Flask app dynamiquement
    module_name, create_app_fn = APP_IMPORT_STRING.split(":")
    app_mod = importlib.import_module(module_name)
    app = getattr(app_mod, create_app_fn)()

    structure = scan_project_structure("app")
    routes = extract_flask_routes(app)
    models = extract_models_info()
    forms = extract_forms_info()
    ctx_vars = extract_context_processors(app)
    vars_jinja, macros_jinja = extract_jinja_vars_macros(TEMPLATES_DIR)

    with open("ERP_CORE_ARCHITECTURE.md", "w", encoding="utf-8") as f:
        f.write("# 🏪 ERP Fée Maison — Architecture, Cœur Métier & Roadmap\n\n")
        f.write("## 1. Résumé Métier et Contexte\n")
        f.write(SUMMARY + "\n")
        f.write("\n---\n\n## 2. Roadmap et Phases\n")
        f.write(ROADMAP)
        f.write("\n---\n\n## 3. Structure du Projet\n")
        f.write("```\n"+structure+"\n```\n")
        f.write("\n---\n\n## 4. Routes Flask\n")
        for r in routes:
            f.write(f"- `{r['methods']}` {r['rule']} (endpoint: `{r['endpoint']}`, blueprint: `{r['blueprint']}`)\n")
            if r['doc']:
                f.write(f"    - {r['doc']}\n")
        f.write("\n---\n\n## 5. Modèles principaux (entités)\n")
        for m in models:
            f.write(f"- **{m['model']}** ({m['file']}):\n")
            for field in m['fields']:
                f.write(f"    - {field}\n")
        f.write("\n---\n\n## 6. Forms WTForms\n")
        for form in forms:
            f.write(f"- **{form['form']}** ({form['file']}):\n")
            for field in form['fields']:
                f.write(f"    - {field}\n")
        f.write("\n---\n\n## 7. Context processors (variables globales)\n")
        for v in ctx_vars:
            f.write(f"- {v}\n")
        f.write("\n---\n\n## 8. Variables et macros Jinja2 utilisées\n")
        f.write("**Variables** :\n")
        for v in vars_jinja:
            f.write(f"- {v}\n")
        f.write("\n**Macros** :\n")
        for m in macros_jinja:
            f.write(f"- {m}\n")
        f.write("\n\n---\n\n")
        f.write("**Ce document est généré automatiquement pour guider IA et nouveaux contributeurs.**\n")

if __name__ == "__main__":
    main()