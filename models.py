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
    
    # === Gestion 4 Stocks ===
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

    @property
    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet, sérialisable en JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'product_type': self.product_type,
            'unit': self.unit,
            'cost_price': float(self.cost_price) if self.cost_price is not None else 0.0,
            'stock_ingredients_magasin': float(self.stock_ingredients_magasin) if self.stock_ingredients_magasin is not None else 0.0,
        }
    
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
        """Récupère le stock par type de localisation (dans l'unité de base)"""
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
        """Met à jour le stock d'une localisation spécifique. DEPRECATED. Utiliser update_stock_by_location"""
        from app.stock.stock_manager import StockLocationManager
        column_name = StockLocationManager.get_column_name(location_type)
        if column_name:
            current_value = getattr(self, column_name, 0.0)
            new_value = max(0, current_value + quantity_change)
            setattr(self, column_name, new_value)
            self.last_stock_update = datetime.utcnow()
            return True
        return False
    
    def get_location_display_name(self, location_type):
        """Retourne le nom d'affichage de la localisation"""
        names = {
            'comptoir': 'Stock Vente',
            'ingredients_local': 'Labo B',
            'ingredients_magasin': 'Labo A (Réserve)',
            'consommables': 'Stock Consommables'
        }
        return names.get(location_type, location_type.title())

    # ### DEBUT DU BLOC A AJOUTER ###
    from app.stock.stock_manager import StockLocationManager

    def get_stock_by_location(self, location_key: str) -> float:
        """
        Récupère le stock pour un emplacement donné en utilisant le StockLocationManager.
        :param location_key: Le nom de la colonne (ex: 'ingredients_magasin').
        :return: La valeur du stock.
        """
        # La clé est directement le nom de la colonne grâce à notre SelectField
        return getattr(self, location_key, 0.0)

    def update_stock_by_location(self, location_key: str, quantity_change: float) -> bool:
        """
        Met à jour le stock pour un emplacement donné en utilisant le StockLocationManager.
        :param location_key: Le nom de la colonne (ex: 'ingredients_magasin').
        :param quantity_change: La quantité à ajouter (valeur positive) ou à retirer (valeur négative).
        :return: True si la mise à jour a réussi, False sinon.
        """
        if hasattr(self, location_key):
            current_value = getattr(self, location_key, 0.0)
            # On s'assure que le stock ne devient pas négatif
            new_value = max(0, current_value + quantity_change)
            setattr(self, location_key, new_value)
            self.last_stock_update = datetime.utcnow()
            return True
        return False
    # ### FIN DU BLOC A AJOUTER ###

    def get_stock_display(self, location_type='total'):
        """
        Retourne une chaîne de caractères formatée pour l'affichage du stock,
        en convertissant la valeur de base (grammes) vers l'unité d'affichage (KG/L).
        """
        stock_value = 0
        if location_type == 'total':
            stock_value = self.total_stock_all_locations
        else:
            stock_value = self.get_stock_by_location_type(location_type)

        display_unit = self.unit.lower()
        base_unit = self.base_unit_for_recipes()
        
        if stock_value == 0:
            return f"0 {display_unit.upper()}"

        try:
            if display_unit == 'kg' and base_unit == 'g':
                display_value = stock_value / 1000
                return f"{display_value:,.3f} kg".replace(",", " ").replace(".", ",")
            
            if display_unit == 'l' and base_unit == 'ml':
                display_value = stock_value / 1000
                return f"{display_value:,.3f} L".replace(",", " ").replace(".", ",")

            return f"{int(stock_value)} {display_unit}"

        except Exception:
            return f"{stock_value} {base_unit} (brut)"

    def base_unit_for_recipes(self):
        """Détermine l'unité de base pour les calculs de recette."""
        unit_lower = self.unit.lower()
        if unit_lower in ['kg', 'g', 'mg']:
            return 'g'
        if unit_lower in ['l', 'cl', 'ml']:
            return 'ml'
        return unit_lower
    
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
    
    # Nouvelle colonne pour spécifier le lieu de production.
    production_location = db.Column(
        db.String(50), 
        nullable=False, 
        default='ingredients_magasin', 
        server_default='ingredients_magasin'
    )
    
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
    produced_by = db.relationship('Employee', secondary=order_employees, back_populates='orders_produced')
    
    @property
    def order_date(self):
        return self.due_date
    
    def get_items_count(self):
        return self.items.count() if hasattr(self.items, 'count') else len(self.items)
    
    def get_items_total(self):
        return float(sum(item.subtotal for item in self.items))
    
    def get_producers_names(self):
        return [emp.name for emp in self.produced_by]
    
    def get_main_producer(self):
        return self.produced_by[0] if self.produced_by else None
    
    def assign_producer(self, employee):
        if employee not in self.produced_by:
            self.produced_by.append(employee)
    
    def remove_producer(self, employee):
        if employee in self.produced_by:
            self.produced_by.remove(employee)
    
    def get_order_type_display(self):
        order_types = {
            'customer_order': 'Commande Client',
            'counter_production_request': 'Ordre de Production',
            'in_store': 'Vente au Comptoir'
        }
        return order_types.get(self.order_type, self.order_type.title())
    
    def get_status_display(self):
        status_types = {
            'pending': 'En attente',
            'cancelled': 'Annulée',
            'completed': 'Terminée',
            'in_production': 'En production',
            'ready_at_shop': 'Reçue au magasin',
            'out_for_delivery': 'En livraison',
            'delivered': 'Livrée',
            'in_progress': 'En préparation',
            'ready': 'Prête',
            'awaiting_payment': 'En attente de paiement'
        }
        return status_types.get(self.status, self.status.title())
    
    def get_delivery_option_display(self):
        if not self.delivery_option:
            return "Non spécifié"
        
        delivery_options = {
            'pickup': 'Retrait en magasin',
            'delivery': 'Livraison à domicile'
        }
        return delivery_options.get(self.delivery_option, self.delivery_option.title())
    
    def get_status_color_class(self):
        status_colors = {
            'pending': 'secondary',
            'in_production': 'warning',
            'ready_at_shop': 'info',
            'out_for_delivery': 'primary',
            'delivered': 'success',
            'completed': 'success',
            'cancelled': 'danger',
            'awaiting_payment': 'warning'
        }
        return status_colors.get(self.status, 'secondary')
    
    def should_appear_in_calendar(self):
        return self.status in ['pending', 'in_production']
    
    def can_be_received_at_shop(self):
        return self.status == 'in_production'
    
    def can_be_delivered(self):
        return self.status == 'ready_at_shop'
    
    def mark_as_in_production(self):
        if self.status == 'pending':
            self.status = 'in_production'
            return True
        return False
    
    def mark_as_received_at_shop(self):
        if self.status == 'in_production':
            self.status = 'ready_at_shop'
            self._increment_shop_stock()
            return True
        return False
    
    def mark_as_delivered(self):
        if self.status == 'ready_at_shop':
            self.status = 'delivered'
            self._decrement_shop_stock()
            return True
        return False
    
    def _increment_shop_stock(self):
        for item in self.items:
            if item.product:
                item.product.update_stock_location('comptoir', float(item.quantity))
                print(f"📦 Stock comptoir incrémenté: {item.product.name} +{item.quantity}")
    
    def _decrement_shop_stock(self):
        for item in self.items:
            if item.product:
                item.product.update_stock_location('comptoir', -float(item.quantity))
                print(f"📦 Stock comptoir décrémenté: {item.product.name} -{item.quantity}")
    
    def calculate_total_amount(self):
        items_total = Decimal('0.0')
        for item in self.items:
            items_total += item.subtotal
        
        delivery_cost = Decimal(self.delivery_cost or 0)
        self.total_amount = items_total + delivery_cost
        return self.total_amount
    
    def get_items_subtotal(self):
        return sum(item.subtotal for item in self.items)
    
    def get_formatted_due_date(self):
        if self.due_date:
            return self.due_date.strftime('%d/%m/%Y à %H:%M')
        return "Non définie"
    
    def get_formatted_due_date_short(self):
        if self.due_date:
            return self.due_date.strftime('%d/%m à %H:%M')
        return "Non définie"
    
    def is_overdue(self):
        if not self.due_date:
            return False
        return self.due_date < datetime.utcnow() and self.status not in ['completed', 'cancelled', 'delivered']
    
    def get_priority_class(self):
        if self.is_overdue():
            return 'danger'
        elif self.status == 'ready_at_shop':
            return 'success'
        elif self.status == 'in_production':
            return 'warning'
        return 'info'
    
    def __repr__(self):
        return f'<Order {self.id}: {self.customer_name or "Sans nom"}>'
    
    @property
    def items_count(self):
        """Compte le nombre d'items de manière sûre pour les relations lazy."""
        if hasattr(self.items, 'count'):
            return self.items.count()
        return len(self.items)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_subtotal(self):
        return float(Decimal(self.quantity) * Decimal(self.unit_price))
    
    @property
    def price_at_order(self):
        return self.unit_price
    
    @property
    def subtotal(self):
        return Decimal(self.quantity) * Decimal(self.unit_price)
    
    def get_formatted_subtotal(self):
        return f"{self.subtotal:.2f} DA"
    
    def get_formatted_unit_price(self):
        return f"{self.unit_price:.2f} DA"
    
    def get_formatted_quantity(self):
        if self.quantity == int(self.quantity):
            return str(int(self.quantity))
        return f"{self.quantity:.2f}"
    
    def __repr__(self):
        return f'<OrderItem {self.product.name if self.product else "N/A"}: {self.quantity}x{self.unit_price}>'

class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    base_unit = db.Column(db.String(10), nullable=False)
    conversion_factor = db.Column(db.Numeric(10, 3), nullable=False)
    unit_type = db.Column(db.String(20), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ### DEBUT DE LA CORRECTION DÉFINITIVE ###
    @property
    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet, sérialisable en JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'base_unit': self.base_unit,
            'conversion_factor': float(self.conversion_factor),
            'unit_type': self.unit_type,
            'display_order': self.display_order
        }
    # ### FIN DE LA CORRECTION DÉFINITIVE ###
    
    def __repr__(self):
        return f'<Unit {self.name}>'
    
    def to_base_unit(self, quantity):
        return float(quantity) * float(self.conversion_factor)
    
    def from_base_unit(self, base_quantity):
        return float(base_quantity) / float(self.conversion_factor)
    
    @property
    def display_name(self):
        return f"{self.name} ({self.unit_type})"