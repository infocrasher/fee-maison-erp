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
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False)  # 'ingredient', 'finished', 'packaging'
    unit = db.Column(db.String(20), nullable=False)
    unit_cost = db.Column(db.Float, nullable=False, default=0.0)
    stock_quantity = db.Column(db.Float, default=0.0)
    min_stock = db.Column(db.Float, default=0.0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'

# Modèle Recipe
class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    yield_quantity = db.Column(db.Float, nullable=False, default=1.0)
    yield_unit = db.Column(db.String(20), nullable=False, default='pièce')
    prep_time = db.Column(db.Integer)  # en minutes
    cook_time = db.Column(db.Integer)  # en minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_cost(self):
        """Calcule le coût total de la recette"""
        return sum(ing.cost for ing in self.ingredients)
    
    @property
    def cost_per_unit(self):
        """Calcule le coût par unité produite"""
        if self.yield_quantity > 0:
            return self.total_cost / self.yield_quantity
        return 0.0
    
    def __repr__(self):
        return f'<Recipe {self.name}>'

# Modèle RecipeIngredient
class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='recipe_uses')
    
    @property
    def cost(self):
        """Calcule le coût de cet ingrédient dans la recette"""
        if self.product:
            return self.quantity * self.product.unit_cost
        return 0.0
    
    def __repr__(self):
        return f'<RecipeIngredient {self.quantity} {self.unit} of {self.product.name if self.product else "Unknown"}>'
