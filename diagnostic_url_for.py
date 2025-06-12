import os
import re
import sys
import traceback
from typing import List, Tuple
from flask import Flask, url_for
from werkzeug.routing import BuildError
from jinja2 import Environment, FileSystemLoader

# -------- CONFIGURATION --------
# Adapter ces chemins à votre projet si besoin
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(PROJECT_ROOT, "app")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
APP_INIT_PATH = os.path.join(APP_DIR, "__init__.py")

# -------- IMPORT DE L'APPLICATION --------
# On suppose que la factory s'appelle 'create_app' dans app/__init__.py
sys.path.insert(0, PROJECT_ROOT)
from app import create_app  # type: ignore

app: Flask = create_app()

# -------- REGEX POUR url_for --------
# Cette regex doit couvrir les cas url_for('endpoint', ...) et url_for("endpoint", ...)
URL_FOR_REGEX = re.compile(
    r"url_for\(\s*(['\"])([\w\.]+)\1\s*(?:,([^)]*))?\)",
    re.MULTILINE
)

# -------- FONCTIONS UTILITAIRES --------

def find_html_files(root: str) -> List[str]:
    """Renvoie la liste des fichiers .html dans root, récursivement."""
    html_files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith('.html'):
                html_files.append(os.path.join(dirpath, f))
    return html_files

def extract_url_for_calls(filepath: str) -> List[Tuple[int, str, str, str]]:
    """
    Renvoie une liste de tuples (line_number, full_match, endpoint, raw_args)
    pour chaque url_for trouvé dans le fichier.
    """
    calls = []
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    for lineno, line in enumerate(lines, 1):
        for match in URL_FOR_REGEX.finditer(line):
            full_match = match.group(0)
            endpoint = match.group(2)
            raw_args = match.group(3) or ""
            calls.append((lineno, full_match, endpoint, raw_args))
    return calls

def parse_args(raw_args: str):
    """
    Parse les arguments de url_for sous forme de chaîne, retourne un dict.
    Limité aux cas les plus courants: id=1, foo='bar', etc.
    """
    args = {}
    if not raw_args.strip():
        return args
    # Ce n'est pas un vrai parser Python, mais assez robuste pour la majorité des cas simples
    arg_pairs = re.findall(r"(\w+)\s*=\s*(['\"]?[\w\-\./]+['\"]?)", raw_args)
    for key, value in arg_pairs:
        # Nettoyage des guillemets si présents
        value = value.strip('\'"')
        args[key] = value
    return args

def try_build_url(endpoint: str, args: dict):
    with app.app_context():
        with app.test_request_context():
            try:
                url = url_for(endpoint, **args)
                return True, url
            except BuildError as e:
                return False, str(e)
            except Exception as e:
                return False, f"Autre exception: {str(e)}\n{traceback.format_exc()}"

def render_report(invalid, valid):
    print("\n==== DIAGNOSTIC url_for DANS LES TEMPLATES ====\n")
    print("---- ERREURS DÉTECTÉES ----")
    if not invalid:
        print("Aucune erreur url_for détectée ! 🎉")
    else:
        for entry in invalid:
            print(f"Fichier: {entry['file']}, ligne {entry['line']}")
            print(f"  Appel: {entry['call']}")
            print(f"  Erreur: {entry['error']}")
            print("")

    print("---- url_for VALIDES (confirmation) ----")
    for entry in valid:
        print(f"Fichier: {entry['file']}, ligne {entry['line']}")
        print(f"  Appel: {entry['call']} -> {entry['url']}")
    print(f"\nTotal url_for valides : {len(valid)}\n")

def main():
    html_files = find_html_files(TEMPLATES_DIR)
    invalid_url_fors = []
    valid_url_fors = []

    for html_file in html_files:
        calls = extract_url_for_calls(html_file)
        for lineno, call, endpoint, raw_args in calls:
            arg_dict = parse_args(raw_args)
            success, result = try_build_url(endpoint, arg_dict)
            entry = {
                "file": os.path.relpath(html_file, PROJECT_ROOT),
                "line": lineno,
                "call": call
            }
            if success:
                entry["url"] = result
                valid_url_fors.append(entry)
            else:
                entry["error"] = result
                invalid_url_fors.append(entry)

    render_report(invalid_url_fors, valid_url_fors)

if __name__ == "__main__":
    main()