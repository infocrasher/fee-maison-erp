# models.py
from datetime import datetime, timezone 
from decimal import Decimal, InvalidOperation
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user' 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def __repr__(self):
        return f"<User '{self.username}', Email: '{self.email}', Role: '{self.role}'>"
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def is_admin(self): return self.role == 'admin'
    def has_role(self, role_name): return self.role == role_name

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship('Product', backref='category_ref', lazy='dynamic')
    def __repr__(self): return f"<Category '{self.name}'>"

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    product_type = db.Column(db.String(20), nullable=False, default='finished')
    unit = db.Column(db.String(20), nullable=False, default='Unité')
    price = db.Column(db.Numeric(10, 2), nullable=True)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True) 
    sku = db.Column(db.String(50), unique=True, nullable=True, index=True)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    def __repr__(self): return f"<Product '{self.name}', Type: {self.product_type}, Unit: {self.unit}, Price: {self.price} DA>"
    def is_ingredient(self): return self.product_type == 'ingredient'
    def is_finished_product(self): return self.product_type == 'finished'

class Order(db.Model):
    __tablename__ = 'orders' 
    id = db.Column(db.Integer, primary_key=True)
    
    order_type = db.Column(db.String(30), nullable=False, default='customer_order') 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    customer_name = db.Column(db.String(100), nullable=True) # nullable=True
    customer_phone = db.Column(db.String(20), nullable=True)  # nullable=True
    customer_address = db.Column(db.Text, nullable=True)    
    order_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False) 
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00')) 
    status = db.Column(db.String(30), nullable=False, default='pending') 
    notes = db.Column(db.Text, nullable=True) 
    delivery_option = db.Column(db.String(20), nullable=False, default='pickup') 
    due_date = db.Column(db.DateTime, nullable=True) 
    delivery_cost = db.Column(db.Numeric(10, 2), nullable=True, default=Decimal('0.00')) 
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User', backref=db.backref('orders_created_by', lazy='dynamic')) 
    
    def __repr__(self): return f"<Order id={self.id} Type='{self.order_type}' Customer='{self.customer_name}' Status='{self.status}'>"
    
    def get_status_display(self):
        status_map = {
            'pending': 'En attente production',
            'ready_at_shop': 'Reçue au magasin',
            'out_for_delivery': 'En livraison client',
            'completed': 'Terminée',
            'awaiting_payment': 'Attente paiement livreur', 
            'cancelled': 'Annulée'
        }
        return status_map.get(self.status, self.status.capitalize())

    def get_order_type_display(self):
        return {
            'customer_order': 'Commande Client',
            'counter_production_request': 'Production Comptoir'
        }.get(self.order_type, self.order_type.replace('_', ' ').capitalize())

    def get_delivery_option_display(self):
        delivery_map = {'pickup': 'Retrait en Magasin', 'delivery': 'Livraison à Domicile', 'internal_transfer': 'Transfert Interne'}
        return delivery_map.get(self.delivery_option, self.delivery_option.capitalize())
    
    def calculate_total_amount(self):
        items_total = self.get_items_total()
        
        if self.order_type == 'customer_order':
            current_delivery_cost = self.delivery_cost if self.delivery_cost is not None else Decimal('0.00')
            if not isinstance(current_delivery_cost, Decimal): # S'assurer que c'est un Decimal
                try: current_delivery_cost = Decimal(str(current_delivery_cost))
                except InvalidOperation: current_delivery_cost = Decimal('0.00')
            
            if self.delivery_option == 'delivery':
                self.total_amount = items_total + current_delivery_cost
            else: # 'pickup' pour une commande client
                self.total_amount = items_total
        else: # 'counter_production_request'
            # Pour une production comptoir, le "total_amount" ne représente pas une vente.
            # Nous le mettons à zéro pour éviter toute confusion.
            # La valeur des produits fabriqués pour le stock sera gérée ailleurs (valorisation de stock).
            self.total_amount = Decimal('0.00') 
        return self.total_amount

    def get_items_count(self): return sum(item.quantity for item in self.items.all())
    def get_items_total(self): return sum(item.get_subtotal() for item in self.items.all())

class OrderItem(db.Model):
    __tablename__ = 'order_items' 
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False) 
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False) 
    quantity = db.Column(db.Integer, nullable=False) 
    price_at_order = db.Column(db.Numeric(10, 2), nullable=False) 
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    product = db.relationship('Product', backref=db.backref('product_order_items', lazy='dynamic'))
    def __repr__(self): return f"<OrderItem id={self.id} OrderId={self.order_id} ProductId={self.product_id} Qty={self.quantity}>"
    def get_subtotal(self): return Decimal(str(self.quantity)) * self.price_at_order