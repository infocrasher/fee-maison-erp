import os
import re

# Mapping exhaustif basé sur ton tableau. NE PAS mettre 'dashboard' ici car il est ambigu.
ENDPOINT_MAPPING = {
    # main
    "hello_world": "main.hello_world",
    # auth
    "login": "auth.login",
    "logout": "auth.logout",
    "account": "auth.account",
    # admin
    # PAS de "dashboard" ici à cause de l'ambiguïté
    # products
    "list_products": "products.list_products",
    "new_product": "products.new_product",
    "view_product": "products.view_product",
    "edit_product": "products.edit_product",
    "delete_product": "products.delete_product",
    "list_categories": "products.list_categories",
    "new_category": "products.new_category",
    "edit_category": "products.edit_category",
    "delete_category": "products.delete_category",
    # orders
    "list_orders": "orders.list_orders",
    "new_order": "orders.new_order",
    "view_order": "orders.view_order",
    "edit_order": "orders.edit_order",
    "edit_order_status": "orders.edit_order_status",
    "orders_calendar": "orders.orders_calendar",
    # recipes
    "list_recipes": "recipes.list_recipes",
    "new_recipe": "recipes.new_recipe",
    "view_recipe": "recipes.view_recipe",
    "edit_recipe": "recipes.edit_recipe",
    "delete_recipe": "recipes.delete_recipe",
    # stock
    "overview": "stock.overview",
    "quick_entry": "stock.quick_entry",
    "adjustment": "stock.adjustment",
    # static
    "static": "static",
}

AMBIGUOUS_ENDPOINTS = {"dashboard"}

TEMPLATES_DIR = "app/templates"
EXTENSIONS = {".html", ".jinja2"}

URLFOR_RE = re.compile(r"""
    url_for         # url_for
    \s*\(           # (
    \s*(['"])       # ' ou "
    ([\w\.]+)       # nom de l'endpoint (lettres, chiffres, points)
    \1              # même guillemet
""", re.VERBOSE)

def rewrite_urlfor(string, mapping, ambiguous):
    """
    Remplace tous les endpoints non ambigus par ceux du mapping dans une chaîne (template).
    Renvoie aussi la liste des occurrences ambigües trouvées (ligne, texte).
    """
    lines = string.splitlines()
    ambiguous_found = []

    def repl(match):
        endpoint = match.group(2)
        # Si déjà blueprint.endpoint, on ne touche pas
        if "." in endpoint:
            return match.group(0)
        # Si ambigu, on note pour rapport
        if endpoint in ambiguous:
            return match.group(0)
        # Sinon, si dans mapping, on remplace
        if endpoint in mapping:
            new_endpoint = mapping[endpoint]
            return match.group(0).replace(endpoint, new_endpoint, 1)
        # Sinon, on laisse tel quel
        return match.group(0)

    # On parcourt ligne par ligne pour trouver les ambiguïtés
    for i, line in enumerate(lines, 1):
        for match in URLFOR_RE.finditer(line):
            endpoint = match.group(2)
            if endpoint in ambiguous:
                ambiguous_found.append((i, line.strip()))

    # Remplacement dans tout le fichier
    new_string = URLFOR_RE.sub(repl, string)
    return new_string, ambiguous_found

def process_file(filepath, mapping, ambiguous):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    new_content, ambiguous_found = rewrite_urlfor(content, mapping, ambiguous)
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Modifié: {filepath}")
    if ambiguous_found:
        for lineno, line in ambiguous_found:
            print(f"AMBIGUÏTÉ: {filepath}, ligne {lineno}: {line}")

def main():
    print("== Remplacement des url_for non ambigus et détection des cas ambiguës ==\n")
    for root, _, files in os.walk(TEMPLATES_DIR):
        for fname in files:
            if os.path.splitext(fname)[1] in EXTENSIONS:
                process_file(os.path.join(root, fname), ENDPOINT_MAPPING, AMBIGUOUS_ENDPOINTS)
    print("\n== Fin. Corrigez manuellement toutes les lignes listées comme 'AMBIGUÏTÉ' selon le contexte ==")

if __name__ == "__main__":
    main()