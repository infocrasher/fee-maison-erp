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
  - js/
    - main.js
  - img/
- templates/
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
- orders/
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- stock/
  - __init__.py
  - forms.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - forms.cpython-313.pyc
    - __init__.cpython-313.pyc
- main/
  - __init__.py
  - routes.py
  - __pycache__/
    - routes.cpython-313.pyc
    - __init__.cpython-313.pyc
```

---

## 4. Routes Flask
- `GET` /home (endpoint: `main.hello_world`, blueprint: `main`)
- `GET` / (endpoint: `main.hello_world`, blueprint: `main`)
- `GET` /dashboard (endpoint: `main.dashboard`, blueprint: `main`)
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
- `GET,POST` /admin/stock/quick_entry (endpoint: `stock.quick_entry`, blueprint: `stock`)
- `GET,POST` /admin/stock/adjustment (endpoint: `stock.adjustment`, blueprint: `stock`)
- `GET` /admin/dashboard (endpoint: `admin.dashboard`, blueprint: `admin`)

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
- categories
- category
- current_year
- div_class
- error
- events
- field
- ingredient_products_json
- legend
- low_stock_products
- manual_csrf_token
- message
- out_of_stock_products
- page_num
- products_serializable
- render_field
- render_pagination
- status_class
- super
- title
- total_orders_on_calendar
- total_products_count
- url_for

**Macros** :
- render_checkbox
- render_field
- render_submit


---

**Ce document est généré automatiquement pour guider IA et nouveaux contributeurs.**
