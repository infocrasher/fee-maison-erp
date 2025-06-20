from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from flask_login import UserMixin
from extensions import db

# Import de la table de liaison depuis employees
from app.employees.models import order_employees

CONVERSION_FACTORS = {
    'kg_g': 1000, 'g_kg': 0.001,
    'l_ml': 1000, 'ml_l': 0.001,
}

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    product_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 2))
    unit = db.Column(db.String(20), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    quantity_in_stock = db.Column(db.Float, default=0.0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # === NOUVEAU : Gestion 4 Stocks ===
    stock_comptoir = db.Column(db.Float, default=0.0, nullable=False)
    stock_ingredients_local = db.Column(db.Float, default=0.0, nullable=False) 
    stock_ingredients_magasin = db.Column(db.Float, default=0.0, nullable=False)
    stock_consommables = db.Column(db.Float, default=0.0, nullable=False)
    
    # Seuils d'alerte par stock
    seuil_min_comptoir = db.Column(db.Float, default=0.0)
    seuil_min_ingredients_local = db.Column(db.Float, default=0.0)
    seuil_min_ingredients_magasin = db.Column(db.Float, default=0.0)
    seuil_min_consommables = db.Column(db.Float, default=0.0)
    
    # Date dernière mise à jour stock
    last_stock_update = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    
    # === NOUVELLES MÉTHODES UTILITAIRES ===
    
    @property
    def total_stock_all_locations(self):
        """Stock total toutes localisations confondues"""
        return (self.stock_comptoir + self.stock_ingredients_local + 
                self.stock_ingredients_magasin + self.stock_consommables)
    
    @property
    def stock_value_total(self):
        """Valeur totale du stock (toutes localisations)"""
        cost = self.cost_price or 0.0
        return float(self.total_stock_all_locations) * float(cost)
    
    def get_stock_by_location_type(self, location_type):
        """Récupère le stock par type de localisation"""
        location_mapping = {
            'comptoir': self.stock_comptoir,
            'ingredients_local': self.stock_ingredients_local,
            'ingredients_magasin': self.stock_ingredients_magasin,
            'consommables': self.stock_consommables
        }
        return location_mapping.get(location_type, 0.0)
    
    def get_seuil_min_by_location(self, location_type):
        """Récupère le seuil minimum par localisation"""
        seuil_mapping = {
            'comptoir': self.seuil_min_comptoir or 0.0,
            'ingredients_local': self.seuil_min_ingredients_local or 0.0,
            'ingredients_magasin': self.seuil_min_ingredients_magasin or 0.0,
            'consommables': self.seuil_min_consommables or 0.0
        }
        return seuil_mapping.get(location_type, 0.0)
    
    def is_low_stock_by_location(self, location_type):
        """Vérifie si le stock est faible pour une localisation"""
        current_stock = self.get_stock_by_location_type(location_type)
        min_threshold = self.get_seuil_min_by_location(location_type)
        return current_stock <= min_threshold
    
    def get_low_stock_locations(self):
        """Retourne la liste des localisations en stock faible"""
        locations = ['comptoir', 'ingredients_local', 'ingredients_magasin', 'consommables']
        return [loc for loc in locations if self.is_low_stock_by_location(loc)]
    
    def update_stock_location(self, location_type, quantity_change):
        """Met à jour le stock d'une localisation spécifique"""
        if location_type == 'comptoir':
            self.stock_comptoir = max(0, self.stock_comptoir + quantity_change)
        elif location_type == 'ingredients_local':
            self.stock_ingredients_local = max(0, self.stock_ingredients_local + quantity_change)
        elif location_type == 'ingredients_magasin':
            self.stock_ingredients_magasin = max(0, self.stock_ingredients_magasin + quantity_change)
        elif location_type == 'consommables':
            self.stock_consommables = max(0, self.stock_consommables + quantity_change)
        
        self.last_stock_update = datetime.utcnow()
        return True
    
    def get_location_display_name(self, location_type):
        """Retourne le nom d'affichage de la localisation"""
        names = {
            'comptoir': 'Stock Comptoir',
            'ingredients_local': 'Stock Local Production',
            'ingredients_magasin': 'Stock Magasin',
            'consommables': 'Stock Consommables'
        }
        return names.get(location_type, location_type.title())
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, unique=True)
    yield_quantity = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    yield_unit = db.Column(db.String(50), nullable=False, default='pièces', server_default='pièces')
    preparation_time = db.Column(db.Integer)
    cooking_time = db.Column(db.Integer)
    difficulty_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    finished_product = db.relationship('Product', foreign_keys=[product_id], backref=db.backref('recipe_definition', uselist=False))
    
    @property
    def total_cost(self):
        return sum(ing.cost for ing in self.ingredients)
    
    @property
    def cost_per_unit(self):
        return self.total_cost / Decimal(self.yield_quantity) if self.yield_quantity > 0 else Decimal('0.0')
    
    def __repr__(self):
        return f'<Recipe {self.name}>'

class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_needed = db.Column(db.Numeric(10, 3), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='recipe_uses')
    
    def _convert_unit_cost(self):
        """Convertit le coût unitaire selon les unités utilisées"""
        if not self.product or not self.product.cost_price:
            return Decimal('0.0')
        
        product_unit = self.product.unit.upper()
        recipe_unit = self.unit.upper()
        base_cost = Decimal(self.product.cost_price)
        
        if product_unit == recipe_unit:
            return base_cost
        
        conversions = {
            ('KG', 'G'): base_cost / 1000,
            ('L', 'ML'): base_cost / 1000,
            ('G', 'KG'): base_cost * 1000,
            ('ML', 'L'): base_cost * 1000,
            ('KG', 'MG'): base_cost / 1000000,
            ('L', 'CL'): base_cost / 100,
        }
        
        conversion_key = (product_unit, recipe_unit)
        if conversion_key in conversions:
            return conversions[conversion_key]
        
        print(f"⚠️ Conversion non trouvée: {product_unit} → {recipe_unit} pour {self.product.name}")
        return base_cost
    
    @property
    def cost(self):
        """Calcule le coût de cet ingrédient avec conversion d'unités"""
        if not self.product or not self.product.cost_price:
            return Decimal('0.0')
        
        converted_cost_per_unit = self._convert_unit_cost()
        return Decimal(self.quantity_needed) * converted_cost_per_unit
    
    def __repr__(self):
        return f'<RecipeIngredient {self.recipe.name} - {self.product.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    order_type = db.Column(db.String(50), nullable=False, default='customer_order')
    customer_name = db.Column(db.String(200))
    customer_phone = db.Column(db.String(20))
    customer_address = db.Column(db.Text)
    delivery_option = db.Column(db.String(20), default='pickup')
    due_date = db.Column(db.DateTime, nullable=False)
    delivery_cost = db.Column(db.Numeric(10, 2), default=0.0)
    status = db.Column(db.String(50), default='pending', index=True)
    notes = db.Column(db.Text)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    # ✅ NOUVELLE RELATION : Tracking employés de production
    produced_by = db.relationship('Employee', secondary=order_employees, back_populates='orders_produced')
    
    # ✅ CORRECTION : Propriété order_date (alias pour due_date)
    @property
    def order_date(self):
        """Alias pour due_date - compatibilité avec templates existants"""
        return self.due_date
    
    # ✅ CORRECTION : Méthode get_items_count manquante
    def get_items_count(self):
        """Retourne le nombre d'items dans la commande"""
        return self.items.count() if hasattr(self.items, 'count') else len(self.items)
    
    # ✅ CORRECTION : Méthode get_items_total manquante
    def get_items_total(self):
        """Retourne le total des articles (méthode pour compatibilité template)"""
        return float(sum(item.subtotal for item in self.items))
    
    # ✅ NOUVELLE MÉTHODE : Gestion employés de production
    def get_producers_names(self):
        """Retourne les noms des employés qui ont produit cette commande"""
        return [emp.name for emp in self.produced_by]
    
    def get_main_producer(self):
        """Retourne le premier employé assigné (producteur principal)"""
        return self.produced_by[0] if self.produced_by else None
    
    def assign_producer(self, employee):
        """Assigne un employé à la production de cette commande"""
        if employee not in self.produced_by:
            self.produced_by.append(employee)
    
    def remove_producer(self, employee):
        """Retire un employé de la production de cette commande"""
        if employee in self.produced_by:
            self.produced_by.remove(employee)
    
    # ✅ CORRECTION : Méthodes d'affichage pour templates
    def get_order_type_display(self):
        """Retourne le libellé lisible du type de commande"""
        order_types = {
            'customer_order': 'Commande Client',
            'counter_production_request': 'Ordre de Production',
            'in_store': 'Vente au Comptoir'
        }
        return order_types.get(self.order_type, self.order_type.title())
    
    def get_status_display(self):
        """Retourne le libellé lisible du statut - VERSION ÉTENDUE"""
        status_types = {
            # États généraux
            'pending': 'En attente',
            'cancelled': 'Annulée',
            'completed': 'Terminée',
            
            # ✅ NOUVEAUX ÉTATS - Workflow production
            'in_production': 'En production',  # → Calendrier Rayan
            'ready_at_shop': 'Reçue au magasin',  # → Yasmine peut livrer
            'out_for_delivery': 'En livraison',  # → En cours de livraison
            'delivered': 'Livrée',  # → Stock décrementé
            
            # États existants (compatibilité)
            'in_progress': 'En préparation',
            'ready': 'Prête',
            'awaiting_payment': 'En attente de paiement'
        }
        return status_types.get(self.status, self.status.title())
    
    def get_delivery_option_display(self):
        """Retourne le libellé lisible de l'option de livraison"""
        if not self.delivery_option:
            return "Non spécifié"
        
        delivery_options = {
            'pickup': 'Retrait en magasin',
            'delivery': 'Livraison à domicile'
        }
        return delivery_options.get(self.delivery_option, self.delivery_option.title())
    
    def get_status_color_class(self):
        """Retourne la classe CSS selon le statut pour l'affichage"""
        status_colors = {
            'pending': 'secondary',
            'in_production': 'warning',  # Orange pour Rayan
            'ready_at_shop': 'info',  # Bleu pour Yasmine
            'out_for_delivery': 'primary',  # Bleu foncé en livraison
            'delivered': 'success',  # Vert livré
            'completed': 'success',
            'cancelled': 'danger',
            'awaiting_payment': 'warning'
        }
        return status_colors.get(self.status, 'secondary')
    
    # ✅ WORKFLOW METHODS - Gestion des états
    def should_appear_in_calendar(self):
        """Détermine si la commande doit apparaître dans le calendrier"""
        # Seules les commandes en production apparaissent pour Rayan
        return self.status in ['pending', 'in_production']
    
    def can_be_received_at_shop(self):
        """Vérifie si la commande peut être reçue au magasin"""
        return self.status == 'in_production'
    
    def can_be_delivered(self):
        """Vérifie si la commande peut être livrée/vendue"""
        return self.status == 'ready_at_shop'
    
    def mark_as_in_production(self):
        """Marque la commande comme en production"""
        if self.status == 'pending':
            self.status = 'in_production'
            return True
        return False
    
    def mark_as_received_at_shop(self):
        """Marque la commande comme reçue au magasin + incrémente stock"""
        if self.status == 'in_production':
            self.status = 'ready_at_shop'
            self._increment_shop_stock()
            return True
        return False
    
    def mark_as_delivered(self):
        """Marque la commande comme livrée + décrémente stock"""
        if self.status == 'ready_at_shop':
            self.status = 'delivered'
            self._decrement_shop_stock()
            return True
        return False
    
    def _increment_shop_stock(self):
        """Incrémente le stock comptoir quand la commande arrive au magasin"""
        for item in self.items:
            if item.product:
                # MODIFICATION : Utiliser le nouveau système 4 stocks
                item.product.update_stock_location('comptoir', float(item.quantity))
                # Log du mouvement
                print(f"📦 Stock comptoir incrémenté: {item.product.name} +{item.quantity}")
    
    def _decrement_shop_stock(self):
        """Décrémente le stock comptoir quand la commande est livrée"""
        for item in self.items:
            if item.product:
                # MODIFICATION : Utiliser le nouveau système 4 stocks
                item.product.update_stock_location('comptoir', -float(item.quantity))
                # Log du mouvement
                print(f"📦 Stock comptoir décrémenté: {item.product.name} -{item.quantity}")
    
    # ✅ CORRECTION : Méthode calculate_total_amount manquante
    def calculate_total_amount(self):
        """Calcule et met à jour le montant total de la commande"""
        items_total = Decimal('0.0')
        for item in self.items:
            items_total += item.subtotal
        
        delivery_cost = Decimal(self.delivery_cost or 0)
        self.total_amount = items_total + delivery_cost
        return self.total_amount
    
    def get_items_subtotal(self):
        """Retourne le sous-total des articles (sans frais de livraison)"""
        return sum(item.subtotal for item in self.items)
    
    def get_formatted_due_date(self):
        """Retourne la date et heure formatées pour affichage"""
        if self.due_date:
            return self.due_date.strftime('%d/%m/%Y à %H:%M')
        return "Non définie"
    
    def get_formatted_due_date_short(self):
        """Retourne la date et heure formatées courte"""
        if self.due_date:
            return self.due_date.strftime('%d/%m à %H:%M')
        return "Non définie"
    
    def is_overdue(self):
        """Vérifie si la commande est en retard"""
        if not self.due_date:
            return False
        return self.due_date < datetime.utcnow() and self.status not in ['completed', 'cancelled', 'delivered']
    
    def get_priority_class(self):
        """Retourne la classe CSS selon la priorité/urgence"""
        if self.is_overdue():
            return 'danger'
        elif self.status == 'ready_at_shop':
            return 'success'
        elif self.status == 'in_production':
            return 'warning'
        return 'info'
    
    def __repr__(self):
        return f'<Order {self.id}: {self.customer_name or "Sans nom"}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ✅ CORRECTION : Ajouter cette méthode manquante
    def get_subtotal(self):
        """Retourne le sous-total (méthode pour compatibilité template)"""
        return float(Decimal(self.quantity) * Decimal(self.unit_price))
    
    # ✅ CORRECTION : Propriété price_at_order
    @property
    def price_at_order(self):
        """Alias pour unit_price - compatibilité avec templates existants"""
        return self.unit_price
    
    @property
    def subtotal(self):
        """Calcule le sous-total de la ligne (propriété)"""
        return Decimal(self.quantity) * Decimal(self.unit_price)
    
    def get_formatted_subtotal(self):
        """Retourne le sous-total formaté"""
        return f"{self.subtotal:.2f} DA"
    
    def get_formatted_unit_price(self):
        """Retourne le prix unitaire formaté"""
        return f"{self.unit_price:.2f} DA"
    
    def get_formatted_quantity(self):
        """Retourne la quantité formatée"""
        if self.quantity == int(self.quantity):
            return str(int(self.quantity))
        return f"{self.quantity:.2f}"
    
    def __repr__(self):
        return f'<OrderItem {self.product.name if self.product else "N/A"}: {self.quantity}x{self.unit_price}>'

class Unit(db.Model):
    """
    Unités de conditionnement prédéfinies (25kg, 5L, 250g, etc.)
    Permet de gérer les achats selon les conditionnements réels des fournisseurs
    """
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # "25kg", "5L"
    base_unit = db.Column(db.String(10), nullable=False)         # "g", "ml"
    conversion_factor = db.Column(db.Numeric(10, 3), nullable=False)  # 25000, 5000
    unit_type = db.Column(db.String(20), nullable=False)         # "weight", "volume"
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Unit {self.name}>'
    
    def to_base_unit(self, quantity):
        """Convertit une quantité vers l'unité de base (grammes ou ml)"""
        return float(quantity) * float(self.conversion_factor)
    
    def from_base_unit(self, base_quantity):
        """Convertit depuis l'unité de base vers cette unité"""
        return float(base_quantity) / float(self.conversion_factor)
    
    @property
    def display_name(self):
        """Nom d'affichage avec type d'unité"""
        return f"{self.name} ({self.unit_type})"
