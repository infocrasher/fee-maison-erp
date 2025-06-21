# 🏪 ERP Fée Maison — Architecture, Cœur Métier & Roadmap

## 1. Résumé Métier et Contexte

### 🏪 Nature de l'Activité

"Fée Maison" est une entreprise de production et vente de produits alimentaires artisanaux opérant sur deux sites :
- Magasin principal : Vente au comptoir et prise de commandes
- Local de production : Fabrication des produits (200m du magasin)
...


---

## 2. Roadmap et Phases

## 🚩 Roadmap ERP Fée Maison

✅ PHASE 1 : FOUNDATION (TERMINÉE)
🏗️ Infrastructure de Base
...
TOTAL RESTANT : 25-33 semaines (6-8 mois)

🏆 Objectif Final
ERP complet et autonome pour Fée Maison avec toutes les fonctionnalités métier, hébergé localement avec accès web via nom de domaine, formation complète des utilisatrices et documentation exhaustive.

---

## 3. Structure du Projet
```
- app/
  - __init__.py
- purchases/
  - models.py
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - models.cpython-313.pyc
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- products/
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- auth/
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- templates_backup/
  - _form_macros.html
  - base.html
  - products/
    - list_categories.html
    - product_form.html
    - list_products.html
    - view_product.html
    - category_form.html
  - auth/
    - login.html
    - account.html
  - admin/
    - admin_dashboard.html
  - recipes/
    - recipe_form.html
    - list_recipes.html
    - view_recipe.html
  - orders/
    - order_form.html
    - view_order.html
    - order_form_multifield.html
    - order_status_form.html
    - orders_calendar.html
    - list_orders.html
  - errors/
    - 403.html
    - 500.html
    - 404.html
  - stock/
    - stock_overview.html
    - quick_stock_entry.html
    - stock_adjustment_form.html
  - main/
    - home.html
    - dashboard.html
- admin/
  - __init__.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - __init__.cpython-313.pyc
- __pycache__/
  - __init__.cpython-313.pyc
- recipes/
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- static/
  - css/
    - style.css
    - dashboards/
      - shop.css
      - production.css
  - js/
    - main.js
    - dashboards/
      - production.js
      - shop.js
      - notifications.js
  - img/
- templates/
  - _form_macros.html
  - base.html
  - purchases/
    - edit_purchase.html
    - mark_paid.html
    - new_purchase.html
    - list_purchases.html
    - view_purchase.html
  - products/
    - list_categories.html
    - product_form.html
    - list_products.html
    - view_product.html
    - category_form.html
  - auth/
    - login.html
    - account.html
  - admin/
    - admin_dashboard.html
  - dashboards/
    - ingredients_alerts.html
    - production_dashboard.html
    - shop_dashboard.html
  - recipes/
    - recipe_form.html
    - list_recipes.html
    - view_recipe.html
  - orders/
    - order_form.html
    - view_order.html
    - order_form_multifield.html
    - order_status_form.html
    - production_order_form.html
    - customer_order_form.html
    - orders_calendar.html
    - change_status_form.html
    - list_orders.html
  - errors/
    - 403.html
    - 500.html
    - 404.html
  - stock/
    - transfers.html
    - dashboard_comptoir.html
    - dashboard_local.html
    - movements_history.html
    - stock_overview.html
    - dashboard_magasin.html
    - dashboard_consommables.html
    - quick_stock_entry.html
    - stock_adjustment_form.html
  - main/
    - home.html
    - dashboard.html
  - employees/
    - employee_form.html
    - list_employees.html
    - view_employee.html
- orders/
  - dashboard_routes.py
  - __init__.py
  - forms.py
  - status_routes.py
  - routes.py
  - __pycache__/
    - dashboard_routes.cpython-313.pyc
    - status_routes.cpython-313.pyc
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- stock/
  - models.py
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - models.cpython-313.pyc
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- main/
  - __init__.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - __init__.cpython-313.pyc
- employees/
  - models.py
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - models.cpython-313.pyc
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
```

---

## 4. Routes Flask
- `GET` /home (endpoint: `main.hello_world`, blueprint: `main`)
- `GET` / (endpoint: `main.hello_world`, blueprint: `main`)
- `GET` /dashboard (endpoint: `main.dashboard`, blueprint: `main`)
    - Dashboard principal avec statistiques
- `GET,POST` /auth/login (endpoint: `auth.login`, blueprint: `auth`)
- `GET` /auth/logout (endpoint: `auth.logout`, blueprint: `auth`)
- `GET,POST` /auth/account (endpoint: `auth.account`, blueprint: `auth`)
- `GET` /admin/products/categories (endpoint: `products.list_categories`, blueprint: `products`)
- `GET,POST` /admin/products/category/new (endpoint: `products.new_category`, blueprint: `products`)
- `GET,POST` /admin/products/category/<int:category_id>/edit (endpoint: `products.edit_category`, blueprint: `products`)
- `POST` /admin/products/category/<int:category_id>/delete (endpoint: `products.delete_category`, blueprint: `products`)
- `GET` /admin/products/ (endpoint: `products.list_products`, blueprint: `products`)
- `GET` /admin/products/<int:product_id> (endpoint: `products.view_product`, blueprint: `products`)
- `GET,POST` /admin/products/new (endpoint: `products.new_product`, blueprint: `products`)
- `GET,POST` /admin/products/<int:product_id>/edit (endpoint: `products.edit_product`, blueprint: `products`)
- `POST` /admin/products/<int:product_id>/delete (endpoint: `products.delete_product`, blueprint: `products`)
- `GET` /admin/orders/ (endpoint: `orders.list_orders`, blueprint: `orders`)
- `GET` /admin/orders/customer (endpoint: `orders.list_customer_orders`, blueprint: `orders`)
- `GET` /admin/orders/production (endpoint: `orders.list_production_orders`, blueprint: `orders`)
- `GET` /admin/orders/api/products (endpoint: `orders.api_products`, blueprint: `orders`)
- `GET,POST` /admin/orders/customer/new (endpoint: `orders.new_customer_order`, blueprint: `orders`)
- `GET,POST` /admin/orders/production/new (endpoint: `orders.new_production_order`, blueprint: `orders`)
- `GET,POST` /admin/orders/new (endpoint: `orders.new_order`, blueprint: `orders`)
- `GET` /admin/orders/<int:order_id> (endpoint: `orders.view_order`, blueprint: `orders`)
- `GET,POST` /admin/orders/<int:order_id>/edit (endpoint: `orders.edit_order`, blueprint: `orders`)
- `GET,POST` /admin/orders/<int:order_id>/edit_status (endpoint: `orders.edit_order_status`, blueprint: `orders`)
- `GET` /admin/orders/calendar (endpoint: `orders.orders_calendar`, blueprint: `orders`)
- `GET` /admin/recipes/ (endpoint: `recipes.list_recipes`, blueprint: `recipes`)
- `GET` /admin/recipes/<int:recipe_id> (endpoint: `recipes.view_recipe`, blueprint: `recipes`)
- `GET,POST` /admin/recipes/new (endpoint: `recipes.new_recipe`, blueprint: `recipes`)
- `GET,POST` /admin/recipes/<int:recipe_id>/edit (endpoint: `recipes.edit_recipe`, blueprint: `recipes`)
- `POST` /admin/recipes/<int:recipe_id>/delete (endpoint: `recipes.delete_recipe`, blueprint: `recipes`)
- `GET` /admin/stock/overview (endpoint: `stock.overview`, blueprint: `stock`)
    - Vue d'ensemble globale des 4 stocks
- `GET,POST` /admin/stock/quick_entry (endpoint: `stock.quick_entry`, blueprint: `stock`)
    - Réception rapide avec sélection de localisation
- `GET,POST` /admin/stock/adjustment (endpoint: `stock.adjustment`, blueprint: `stock`)
    - Ajustement de stock avec sélection de localisation
- `GET` /admin/stock/dashboard/magasin (endpoint: `stock.dashboard_magasin`, blueprint: `stock`)
    - Dashboard Stock Magasin - Interface Amel
- `GET` /admin/stock/dashboard/local (endpoint: `stock.dashboard_local`, blueprint: `stock`)
    - Dashboard Stock Local - Interface Rayan
- `GET` /admin/stock/dashboard/comptoir (endpoint: `stock.dashboard_comptoir`, blueprint: `stock`)
    - Dashboard Stock Comptoir - Interface Yasmine
- `GET` /admin/stock/dashboard/consommables (endpoint: `stock.dashboard_consommables`, blueprint: `stock`)
    - Dashboard Stock Consommables - Interface Amel
- `GET` /admin/stock/transfers (endpoint: `stock.transfers_list`, blueprint: `stock`)
    - Liste des transferts entre stocks
- `GET,POST` /admin/stock/transfers/create (endpoint: `stock.create_transfer`, blueprint: `stock`)
    - Création d'un nouveau transfert
- `POST` /admin/stock/transfers/<int:transfer_id>/approve (endpoint: `stock.approve_transfer`, blueprint: `stock`)
    - Approbation d'un transfert
- `POST` /admin/stock/transfers/<int:transfer_id>/complete (endpoint: `stock.complete_transfer`, blueprint: `stock`)
    - Finalisation d'un transfert avec mise à jour des stocks
- `GET` /admin/stock/api/stock_levels/<int:product_id> (endpoint: `stock.api_stock_levels`, blueprint: `stock`)
    - API pour récupérer les niveaux de stock d'un produit
- `GET` /admin/stock/api/movements_history/<int:product_id> (endpoint: `stock.api_movements_history`, blueprint: `stock`)
    - API pour l'historique des mouvements d'un produit
- `GET` /admin/dashboard (endpoint: `admin.dashboard`, blueprint: `admin`)
- `GET` /admin/purchases/ (endpoint: `purchases.list_purchases`, blueprint: `purchases`)
    - Liste de tous les achats avec filtres et statut paiement
- `GET,POST` /admin/purchases/new (endpoint: `purchases.new_purchase`, blueprint: `purchases`)
    - Création d'un nouveau bon d'achat avec traitement manuel des items et mise à jour stock automatique
- `GET` /admin/purchases/<int:id> (endpoint: `purchases.view_purchase`, blueprint: `purchases`)
    - Affichage détaillé d'un bon d'achat avec unités et paiement
- `GET,POST` /admin/purchases/<int:id>/mark_paid (endpoint: `purchases.mark_as_paid`, blueprint: `purchases`)
    - Marquer un bon d'achat comme payé
- `POST` /admin/purchases/<int:id>/mark_unpaid (endpoint: `purchases.mark_as_unpaid`, blueprint: `purchases`)
    - Marquer un bon d'achat comme non payé
- `POST` /admin/purchases/<int:id>/cancel (endpoint: `purchases.cancel_purchase`, blueprint: `purchases`)
    - Annuler un bon d'achat et reverser le stock
- `GET,POST` /admin/purchases/<int:id>/edit (endpoint: `purchases.edit_purchase`, blueprint: `purchases`)
    - Modification d'un bon d'achat avec support des unités
- `GET` /admin/purchases/api/products_search (endpoint: `purchases.api_products_search`, blueprint: `purchases`)
    - API de recherche de produits pour l'auto-complétion
- `GET` /admin/purchases/api/pending_count (endpoint: `purchases.api_pending_count`, blueprint: `purchases`)
    - API pour le nombre d'achats en attente d'approbation
- `GET` /admin/purchases/api/products/<int:product_id>/units (endpoint: `purchases.api_product_units`, blueprint: `purchases`)
    - API pour récupérer les unités disponibles pour un produit
- `GET` /dashboard/production (endpoint: `dashboard.production_dashboard`, blueprint: `dashboard`)
    - Dashboard de production pour Rayan
- `GET` /dashboard/shop (endpoint: `dashboard.shop_dashboard`, blueprint: `dashboard`)
    - Dashboard magasin pour Yasmine - Gestion des commandes reçues
- `GET` /dashboard/ingredients-alerts (endpoint: `dashboard.ingredients_alerts`, blueprint: `dashboard`)
    - Dashboard alertes ingrédients pour Amel - Gestion des achats
- `GET` /dashboard/admin (endpoint: `dashboard.admin_dashboard`, blueprint: `dashboard`)
    - Dashboard administrateur principal
- `GET` /dashboard/sales (endpoint: `dashboard.sales_dashboard`, blueprint: `dashboard`)
    - Dashboard des ventes
- `GET` /dashboard/api/orders-stats (endpoint: `dashboard.orders_stats_api`, blueprint: `dashboard`)
    - API pour statistiques des commandes en temps réel
- `POST` /orders/<int:order_id>/change-status-to-ready (endpoint: `status.change_status_to_ready`, blueprint: `status`)
    - Change le statut de 'in_production' à 'ready_at_shop' avec sélection employé
- `POST` /orders/<int:order_id>/change-status-to-delivered (endpoint: `status.change_status_to_delivered`, blueprint: `status`)
    - Change le statut de 'ready_at_shop' à 'delivered' pour commandes client
- `GET` /orders/<int:order_id>/select-employees/<string:new_status> (endpoint: `status.select_employees_for_status_change`, blueprint: `status`)
    - Formulaire de sélection des employés pour changement de statut
- `GET,POST` /orders/<int:order_id>/manual-status-change (endpoint: `status.manual_status_change`, blueprint: `status`)
    - Changement de statut manuel pour cas spéciaux
- `GET` /orders/api/active-employees (endpoint: `status.get_active_employees`, blueprint: `status`)
    - API pour récupérer la liste des employés actifs
- `GET` /orders/<int:order_id>/test-employees/<string:new_status> (endpoint: `status.test_employees_no_decorators`, blueprint: `status`)
    - Test sans décorateurs pour isoler le problème
- `GET` /orders/<int:order_id>/test-login/<string:new_status> (endpoint: `status.test_login_only`, blueprint: `status`)
- `GET` /orders/<int:order_id>/test-admin/<string:new_status> (endpoint: `status.test_admin_only`, blueprint: `status`)
- `GET` /orders/<int:order_id>/test-both/<string:new_status> (endpoint: `status.test_both_decorators`, blueprint: `status`)
- `GET` /employees/ (endpoint: `employees.list_employees`, blueprint: `employees`)
    - Liste des employés avec recherche et filtres
- `GET,POST` /employees/new (endpoint: `employees.new_employee`, blueprint: `employees`)
    - Créer un nouvel employé
- `GET` /employees/<int:employee_id> (endpoint: `employees.view_employee`, blueprint: `employees`)
    - Voir les détails d'un employé
- `GET,POST` /employees/<int:employee_id>/edit (endpoint: `employees.edit_employee`, blueprint: `employees`)
    - Modifier un employé
- `POST` /employees/<int:employee_id>/toggle-status (endpoint: `employees.toggle_employee_status`, blueprint: `employees`)
    - Activer/désactiver un employé
- `GET` /employees/api/production-staff (endpoint: `employees.get_production_staff`, blueprint: `employees`)
    - API pour récupérer les employés de production actifs
- `GET` /employees/api/stats (endpoint: `employees.get_employees_stats`, blueprint: `employees`)
    - API pour les statistiques employés

---

## 5. Modèles principaux (entités)

---

## 6. Forms WTForms

---

## 7. Context processors (variables globales)
- csrf_token
- current_user
- current_year
- low_stock_products
- manual_csrf_token
- out_of_stock_products
- total_products_count

---

## 8. Variables et macros Jinja2 utilisées
**Variables** :
- action
- active_employees
- adjustments_this_month
- categories
- category
- critical_consommables
- critical_stock_count
- csrf_token
- div_class
- employees
- employees_count
- error
- estimated_consumption
- events
- field
- ingredient_products_json
- ingredients_needed
- legend
- level_class
- level_icon
- low_stock_products
- manual_csrf_token
- message
- missing_ingredients
- moment
- orders_count
- orders_in_production
- orders_on_time
- orders_overdue
- orders_pending
- orders_ready
- orders_soon
- orders_today
- out_of_stock_products
- page_num
- paid_purchases
- pending_purchases
- production_capacity
- production_staff
- products_count
- products_out_of_stock
- recipes_count
- render_field
- render_pagination
- revenue_today
- sales_today
- seuil
- status_class
- status_text
- stock_level
- super
- title
- total_consommables
- total_employees
- total_ingredients_local
- total_ingredients_magasin
- total_orders
- total_orders_on_calendar
- total_products_comptoir
- total_products_count
- total_purchases
- total_value
- unpaid_purchases
- urgency_class
- urgency_icon
- url_for

**Macros** :
- render_checkbox
- render_field
- render_submit


---

**Ce document est généré automatiquement pour guider IA et nouveaux contributeurs.**
