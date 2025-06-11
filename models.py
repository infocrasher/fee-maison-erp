# --- START OF FILE models.py ---

from datetime import datetime
from decimal import Decimal
# from flask_sqlalchemy import SQLAlchemy  <-- SUPPRIMEZ CETTE LIGNE
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from extensions import db



# Constante pour les conversions, importée par app.py
CONVERSION_FACTORS = {
    'kg_g': 1000, 'g_kg': 0.001,
    'l_ml': 1000, 'ml_l': 0.001,
    # Ajoutez d'autres paires unité source -> unité cible ici
}

# Modèle User
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy='dynamic') # <-- AJOUT: Relation avec les commandes

    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Modèle Category
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

# Modèle Product
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    product_type = db.Column(db.String(50), nullable=False)  # 'finished', 'ingredient'
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))  # Prix de vente
    cost_price = db.Column(db.Numeric(10, 2))  # Prix d'achat/coût
    unit = db.Column(db.String(20), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    quantity_in_stock = db.Column(db.Float, default=0.0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # <-- CORRECTION: Renommage du backref pour la clarté
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.name}>'

# Modèle Recipe
class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), unique=True) # Un produit fini ne peut avoir qu'une recette
    yield_quantity = db.Column(db.Numeric(10, 3), nullable=False, default=1.0)
    yield_unit = db.Column(db.String(50), nullable=False, default='pièces')
    preparation_time = db.Column(db.Integer)
    cooking_time = db.Column(db.Integer)
    difficulty_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    # <-- CORRECTION: Ajout d'un backref pour la relation Recipe -> Product
    finished_product = db.relationship('Product', foreign_keys=[product_id], backref='recipe_definition')
    
    @property
    def total_cost(self):
        return sum(ing.cost for ing in self.ingredients)
    
    @property
    def cost_per_unit(self):
        if self.yield_quantity > 0:
            return self.total_cost / Decimal(self.yield_quantity)
        return Decimal('0.0')
    
    def __repr__(self):
        return f'<Recipe {self.name}>'

# Modèle RecipeIngredient
class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_needed = db.Column(db.Numeric(10, 3), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # <-- CORRECTION: Renommage du backref pour la clarté
    product = db.relationship('Product', backref='recipe_uses')
    
    @property
    def cost(self):
        if self.product and self.product.cost_price:
            return Decimal(self.quantity_needed) * Decimal(self.product.cost_price)
        return Decimal('0.0')
    
    def __repr__(self):
        return f'<RecipeIngredient {self.quantity_needed} {self.unit} of {self.product.name if self.product else "Unknown"}>'

# Modèle Order
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # <-- AJOUT: Lien vers l'utilisateur qui a créé la commande
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
    
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_order_type_display(self): # <-- AJOUT: Méthode utilitaire
        return "Demande Client" if self.order_type == 'customer_order' else "Prod. Comptoir"
        
    def get_status_display(self): # <-- AJOUT: Méthode utilitaire
        statuses = {
            'pending': 'En attente', 'ready_at_shop': 'Prête en boutique',
            'out_for_delivery': 'En livraison', 'completed': 'Terminée',
            'awaiting_payment': 'En attente de paiement', 'cancelled': 'Annulée'
        }
        return statuses.get(self.status, self.status.replace('_', ' ').capitalize())

    # <-- AJOUT: Méthode appelée depuis app.py
    def calculate_total_amount(self):
        """Calcule et met à jour le montant total de la commande."""
        total = sum(item.subtotal for item in self.items)
        if self.delivery_cost:
            total += self.delivery_cost
        self.total_amount = total

    def __repr__(self):
        return f'<Order #{self.id}>'

# Modèle OrderItem
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False) # <-- CORRECTION: Nom standard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    
    def __repr__(self):
        return f'<OrderItem {self.quantity} x {self.product.name if self.product else "Unknown"}>'