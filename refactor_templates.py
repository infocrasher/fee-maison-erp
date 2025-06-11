import os
import re

def replace_url_for_in_html_files(directory, replacements):
    """
    Parcourt récursivement un dossier et remplace les appels url_for()
    dans tous les fichiers .html en utilisant un dictionnaire de mappage.
    """
    files_modified = []
    total_replacements = 0
    
    print(f"🔍 Analyse du dossier : {os.path.abspath(directory)}\n")
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    file_replacements = 0
                    
                    for old, new in replacements.items():
                        # Crée une expression régulière pour trouver url_for('ancienne_route') ou url_for("ancienne_route")
                        # Gère les espaces variables autour des parenthèses et des guillemets.
                        pattern = re.compile(r"url_for\s*\(\s*['\"]" + re.escape(old) + r"['\"]\s*\)")
                        
                        # Compte le nombre de remplacements à faire pour cette route
                        count = len(pattern.findall(content))
                        
                        if count > 0:
                            # Effectue le remplacement
                            content = pattern.sub(f"url_for('{new}')", content)
                            file_replacements += count
                    
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        files_modified.append((filepath, file_replacements))
                        total_replacements += file_replacements
                        
                except Exception as e:
                    print(f"❌ Erreur lors du traitement du fichier {filepath}: {e}")
    
    return files_modified, total_replacements

# ==============================================================================
# 🎯 CONFIGURATION POUR VOTRE PROJET
# ==============================================================================
# Ce dictionnaire mappe les anciens noms de fonction aux nouveaux (avec blueprint)
replacements = {
    # main (routes générales)
    'hello_world': 'main.hello_world',
    'dashboard': 'main.dashboard',

    # auth (authentification)
    'login': 'auth.login',
    'logout': 'auth.logout',
    'account': 'auth.account',
    
    # admin (routes admin générales)
    'admin_dashboard': 'admin.dashboard',
    
    # products & categories
    'list_products': 'products.list_products',
    'view_product': 'products.view_product',
    'new_product': 'products.new_product',
    'edit_product': 'products.edit_product',
    'delete_product': 'products.delete_product',
    'list_categories': 'products.list_categories',
    'new_category': 'products.new_category',
    'edit_category': 'products.edit_category',
    'delete_category': 'products.delete_category',
    
    # orders
    'list_orders': 'orders.list_orders',
    'view_order': 'orders.view_order',
    'new_order': 'orders.new_order',
    'edit_order': 'orders.edit_order',
    'edit_order_status': 'orders.edit_order_status',
    'orders_calendar': 'orders.orders_calendar',

    # recipes
    'list_recipes': 'recipes.list_recipes',
    'view_recipe': 'recipes.view_recipe',
    'new_recipe': 'recipes.new_recipe',
    'edit_recipe': 'recipes.edit_recipe',
    'delete_recipe': 'recipes.delete_recipe',

    # stock
    'overview': 'stock.overview',
    'quick_entry': 'stock.quick_entry',
    'adjustment': 'stock.adjustment',

    # --- Noms de routes potentiellement anciens à mapper ---
    'new_product_route': 'products.new_product' 
}

# 📁 Chemin vers votre dossier de templates
template_dir = './app/templates'

# ==============================================================================
# 🚀 EXÉCUTION DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    print("🔄 Début de la mise à jour des templates...")
    files_changed, total_changes = replace_url_for_in_html_files(template_dir, replacements)

    print("\n" + "="*50)
    print("✅  Opération terminée !")
    print(f"Total des fichiers modifiés : {len(files_changed)}")
    print(f"Total des remplacements   : {total_changes}")
    print("="*50 + "\n")

    if files_changed:
        print("📋 Détail des modifications :")
        for filepath, count in files_changed:
            print(f"  - {filepath} ({count} remplacement(s))")
    else:
        print("ℹ️  Aucun remplacement n'était nécessaire.")