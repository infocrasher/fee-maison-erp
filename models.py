# models.py
from datetime import datetime, timezone, timedelta, date # Ajout de 'date'
from decimal import Decimal, InvalidOperation
from sqlalchemy.ext.hybrid import hybrid_property
from extensions import db 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

CONVERSION_FACTORS = {
    # Poids (base: gramme)
    'g': Decimal('1'),
    'grammes': Decimal('1'),
    'kg': Decimal('1000'),
    'kilogramme': Decimal('1000'),
    # Volume (base: millilitre)
    'ml': Decimal('1'),
    'millilitre': Decimal('1'),
    'cl': Decimal('10'),
    'l': Decimal('1000'),
    'litre': Decimal('1000'),
    # Unités comptables (base: pièce)
    'pièce': Decimal('1'),
    'unité': Decimal('1'),
    'gousse': Decimal('1'),
    'feuille': Decimal('1'),
}

class User(UserMixin, db.Model):
    __tablename__ = 'user' 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    orders_created_by = db.relationship('Order', foreign_keys='Order.user_id', backref='created_by_user', lazy='dynamic')

    def __repr__(self): return f"<User '{self.username}', Email: '{self.email}', Role: '{self.role}'>"
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
    used_in_recipe_lines = db.relationship('RecipeIngredient', foreign_keys='RecipeIngredient.product_id', backref=db.backref('ingredient_product', lazy='joined'), lazy='dynamic')
    purchase_history_entries = db.relationship('PurchaseHistory', foreign_keys='PurchaseHistory.product_id', backref='purchased_product_info', lazy='dynamic')

    def __repr__(self): return f"<Product '{self.name}', Type: {self.product_type}, Unit: {self.unit}, Price: {self.price} DA>"
    def is_ingredient(self): return self.product_type == 'ingredient'
    def is_finished_product(self): return self.product_type == 'finished'

    def get_current_cost(self, calculation_date_param: datetime.date = None) -> Decimal: # Renommé paramètre
        if calculation_date_param is None:
            calculation_date_to_use = datetime.now(timezone.utc).date()
        elif isinstance(calculation_date_param, datetime): 
            calculation_date_to_use = calculation_date_param.date()
        else: # Déjà un objet date
            calculation_date_to_use = calculation_date_param

        if self.product_type == 'ingredient':
            return PurchaseHistory.calculate_weighted_average_cost(self.id, calculation_date_to_use)
        elif self.product_type == 'finished':
            if hasattr(self, 'recipe_definition') and self.recipe_definition:
                return self.recipe_definition.current_total_cost_of_ingredients # Qui utilisera calculation_date_to_use
            else:
                return self.cost_price if self.cost_price is not None else Decimal('0.00')
        return self.cost_price if self.cost_price is not None else Decimal('0.00')

class Order(db.Model):
    __tablename__ = 'orders' 
    id = db.Column(db.Integer, primary_key=True)
    order_type = db.Column(db.String(30), nullable=False, default='customer_order') 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
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
        
    def __repr__(self): return f"<Order id={self.id} Type='{self.order_type}' Customer='{self.customer_name}' Status='{self.status}'>"
    def get_status_display(self):
        status_map = {'pending': 'En attente production', 'ready_at_shop': 'Reçue au magasin','out_for_delivery': 'En livraison client', 'completed': 'Terminée','awaiting_payment': 'Attente paiement livreur', 'cancelled': 'Annulée'}
        return status_map.get(self.status, self.status.capitalize())
    def get_order_type_display(self):
        return {'customer_order': 'Commande Client','counter_production_request': 'Production Comptoir'}.get(self.order_type, self.order_type.replace('_', ' ').capitalize())
    def get_delivery_option_display(self):
        delivery_map = {'pickup': 'Retrait en Magasin', 'delivery': 'Livraison à Domicile', 'internal_transfer': 'Transfert Interne'}
        return delivery_map.get(self.delivery_option, self.delivery_option.capitalize())
    def calculate_total_amount(self):
        items_total = self.get_items_total()
        current_delivery_cost = self.delivery_cost if self.delivery_cost is not None else Decimal('0.00')
        if not isinstance(current_delivery_cost, Decimal):
            try: current_delivery_cost = Decimal(str(current_delivery_cost))
            except InvalidOperation: current_delivery_cost = Decimal('0.00')
        if self.order_type == 'customer_order':
            if self.delivery_option == 'delivery': self.total_amount = items_total + current_delivery_cost
            else: self.total_amount = items_total
        else: self.total_amount = Decimal('0.00') 
        return self.total_amount
    def get_items_count(self): return sum(item.quantity for item in self.items.all())
    def get_items_total(self): return sum(item.get_subtotal() for item in self.items.all())

class OrderItem(db.Model):
    __tablename__ = 'order_items' 
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True) 
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True) 
    quantity = db.Column(db.Integer, nullable=False) 
    price_at_order = db.Column(db.Numeric(10, 2), nullable=False) 
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    product = db.relationship('Product', backref=db.backref('product_order_items', lazy='dynamic'))
    def __repr__(self): return f"<OrderItem id={self.id} OrderId={self.order_id} ProductId={self.product_id} Qty={self.quantity}>"
    def get_subtotal(self): return Decimal(str(self.quantity)) * self.price_at_order

class Recipe(db.Model):
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True) 
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, unique=True, index=True)
    finished_product = db.relationship('Product', backref=db.backref('recipe_definition', uselist=False, lazy='joined', foreign_keys=[product_id]))
    yield_quantity = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('1.00'))
    yield_unit = db.Column(db.String(50), nullable=False, default='pièce') 
    preparation_time = db.Column(db.Integer, nullable=True) 
    cooking_time = db.Column(db.Integer, nullable=True) 
    difficulty_level = db.Column(db.String(50), nullable=True) 
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self): return f"<Recipe '{self.name}' for Product ID {self.product_id}>"

    @hybrid_property
    def current_total_cost_of_ingredients(self) -> Decimal:
        total_cost = Decimal('0.00')
        calculation_date_to_use = datetime.now(timezone.utc).date()

        for item in self.ingredients.all():
            if not item.ingredient_product:
                continue # Ignore les lignes d'ingrédient invalides

            product = item.ingredient_product
            # Obtient le coût du produit par son unité de BASE (ex: 42 DA par KG)
            cost_per_base_unit = product.get_current_cost(calculation_date_to_use)

            # --- DÉBUT DE LA LOGIQUE DE CONVERSION ---
            quantity_in_recipe = item.quantity_needed      # ex: 8000
            unit_in_recipe = item.unit.lower().strip()     # ex: 'g'
            product_base_unit = product.unit.lower().strip() # ex: 'kg'

            # Si les unités sont identiques, pas besoin de convertir
            if unit_in_recipe == product_base_unit:
                quantity_in_base_units = quantity_in_recipe
            else:
                # On trouve les facteurs de conversion pour les deux unités
                factor_from_recipe = CONVERSION_FACTORS.get(unit_in_recipe)
                factor_for_product_base = CONVERSION_FACTORS.get(product_base_unit)

                if factor_from_recipe and factor_for_product_base:
                    # On convertit la quantité de la recette vers l'unité de base du produit
                    # Exemple: (8000 'g' * facteur 1) / (facteur 1000 pour 'kg') = 8 'kg'
                    quantity_in_base_units = (quantity_in_recipe * factor_from_recipe) / factor_for_product_base
                else:
                    # Si une unité est inconnue, on ne peut pas convertir. On ne compte pas le coût pour éviter une erreur.
                    # On pourrait aussi logger une erreur ici.
                    quantity_in_base_units = Decimal('0')

            # On calcule le coût de cet ingrédient et on l'ajoute au total
            # Exemple: 8 'kg' * 42 DA = 336 DA
            item_cost = quantity_in_base_units * cost_per_base_unit
            total_cost += item_cost

        return total_cost

    @hybrid_property
    def current_cost_per_yield_unit(self) -> Decimal:
        if self.yield_quantity is not None and self.yield_quantity != 0:
            return self.current_total_cost_of_ingredients / self.yield_quantity
        return Decimal('0.00')

class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredient'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True) 
    quantity_needed = db.Column(db.Numeric(10, 3), nullable=False)
    unit = db.Column(db.String(50), nullable=False) 
    notes = db.Column(db.String(255), nullable=True) 
    def __repr__(self): return f"<RecipeIngredient PID:{self.product_id} Qty:{self.quantity_needed}{self.unit} for RecipeID:{self.recipe_id}>"

class PurchaseHistory(db.Model):
    __tablename__ = 'purchase_history'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    purchase_date = db.Column(db.Date, nullable=False, index=True, default=lambda: datetime.now(timezone.utc).date())
    quantity_purchased = db.Column(db.Numeric(10, 3), nullable=False)
    unit_of_purchase = db.Column(db.String(50), nullable=False)
    unit_price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False) 
    total_cost_of_purchase = db.Column(db.Numeric(10, 2), nullable=False) 
    supplier_name = db.Column(db.String(150), nullable=True, index=True) 
    invoice_reference = db.Column(db.String(100), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self): return f"<PurchaseHistory PID:{self.product_id} Date:{self.purchase_date} Qty:{self.quantity_purchased} {self.unit_of_purchase}>"

    @staticmethod
    def calculate_weighted_average_cost(product_id: int, target_date_param: datetime.date, months_history: int = 3) -> Decimal: # Renommé paramètre
        # CORRECTION: Utiliser 'date' importé pour isinstance
        if not isinstance(target_date_param, date): 
            try: 
                # Si c'est un datetime, convertir en date
                target_date_to_use = target_date_param.date()
            except AttributeError: 
                # Si ce n'est ni date ni datetime, utiliser aujourd'hui par défaut
                target_date_to_use = datetime.now(timezone.utc).date()
        else: # C'est déjà un objet date
            target_date_to_use = target_date_param

        start_date = target_date_to_use - timedelta(days=months_history * 30)

        purchases = PurchaseHistory.query.filter(
            PurchaseHistory.product_id == product_id,
            PurchaseHistory.purchase_date >= start_date,
            PurchaseHistory.purchase_date <= target_date_to_use
        ).all()

        product = db.session.get(Product, product_id)
        if not product: return Decimal('0.00')
        if not purchases:
            return product.cost_price if product.cost_price is not None else Decimal('0.00')

        total_value_normalized = Decimal('0.00')
        total_quantity_normalized = Decimal('0.00')
        for purchase in purchases:
            quantity_in_base_unit = purchase.quantity_purchased 
            cost_per_base_unit = purchase.unit_price_at_purchase 
            total_value_normalized += quantity_in_base_unit * cost_per_base_unit
            total_quantity_normalized += quantity_in_base_unit
        
        if total_quantity_normalized > 0:
            return total_value_normalized / total_quantity_normalized
        else:
            return product.cost_price if product.cost_price is not None else Decimal('0.00')