from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Modèle User
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    
    # Relations
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

# Modèle Product
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    product_type = db.Column(db.String(50), nullable=False)  # 'finished', 'ingredient' (utilisé dans finished_product_query_factory_for_orders)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))  # Prix de vente (utilisé dans ProductForm)
    cost_price = db.Column(db.Numeric(10, 2))  # Prix d'achat/coût
    unit = db.Column(db.String(20), nullable=False)
    sku = db.Column(db.String(50), unique=True)  # SKU/Référence
    quantity_in_stock = db.Column(db.Integer, default=0)  # Quantité en stock
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'

# Modèle Recipe
class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)  # Instructions
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))  # Produit fini associé
    yield_quantity = db.Column(db.Numeric(10, 3), nullable=False, default=1.0)
    yield_unit = db.Column(db.String(50), nullable=False, default='pièces')
    preparation_time = db.Column(db.Integer)  # en minutes
    cooking_time = db.Column(db.Integer)  # en minutes
    difficulty_level = db.Column(db.String(20))  # 'Facile', 'Moyen', 'Difficile', 'Expert'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    finished_product = db.relationship('Product', foreign_keys=[product_id])
    
    @property
    def total_cost(self):
        """Calcule le coût total de la recette"""
        return sum(ing.cost for ing in self.ingredients)
    
    @property
    def cost_per_unit(self):
        """Calcule le coût par unité produite"""
        if self.yield_quantity > 0:
            return self.total_cost / float(self.yield_quantity)
        return 0.0
    
    def __repr__(self):
        return f'<Recipe {self.name}>'

# Modèle RecipeIngredient
class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_needed = db.Column(db.Numeric(10, 3), nullable=False)  # Quantité nécessaire
    unit = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(255))  # Notes optionnelles
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='recipe_uses')
    
    @property
    def cost(self):
        """Calcule le coût de cet ingrédient dans la recette"""
        if self.product and self.product.cost_price:
            return float(self.quantity_needed) * float(self.product.cost_price)
        return 0.0
    
    def __repr__(self):
        return f'<RecipeIngredient {self.quantity_needed} {self.unit} of {self.product.name if self.product else "Unknown"}>'

# Modèle Order
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    order_type = db.Column(db.String(50), nullable=False, default='customer_order')  # 'customer_order', 'counter_production_request'
    customer_name = db.Column(db.String(200))
    customer_phone = db.Column(db.String(20))
    customer_address = db.Column(db.Text)
    delivery_option = db.Column(db.String(20), default='pickup')  # 'pickup', 'delivery'
    due_date = db.Column(db.DateTime, nullable=False)
    delivery_cost = db.Column(db.Numeric(10, 2), default=0.0)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'ready_at_shop', 'out_for_delivery', 'completed', 'awaiting_payment', 'cancelled'
    notes = db.Column(db.Text)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_cost(self):
        """Calcule le coût total de la commande"""
        return sum(float(item.subtotal) for item in self.items)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

# Modèle OrderItem
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='order_items')
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    
    def __repr__(self):
        return f'<OrderItem {self.quantity} x {self.product.name if self.product else "Unknown"}>'
