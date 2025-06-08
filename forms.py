# forms.py
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, BooleanField, 
                     TextAreaField, DecimalField, IntegerField, SelectField,
                     FieldList, FormField) # Tous les types de champs nécessaires
from wtforms.fields import DateTimeLocalField # Spécifique pour DateTimeLocalField
from wtforms.validators import (DataRequired, Length, Email, EqualTo, 
                                ValidationError, Optional, NumberRange) # Tous les validateurs nécessaires
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_login import current_user
from werkzeug.security import check_password_hash
from decimal import Decimal # Import direct de Decimal

# Import des modèles et de l'instance db
from models import User, Category, Product, Order, OrderItem, Recipe 
from extensions import db 

# --- FACTORIES POUR QUERYSELECTFIELD (EXISTANTES) ---
def category_query_factory():
    return Category.query.order_by(Category.name)

def product_query_factory(): 
    return Product.query.order_by(Product.name)

def finished_product_query_factory_for_orders(): 
    return Product.query.filter_by(product_type='finished').order_by(Product.name)

# --- FACTORIES POUR QUERYSELECTFIELD (NOUVELLES POUR RECETTES) ---
def ingredient_products_factory():
    return Product.query.filter_by(product_type='ingredient').order_by(Product.name)

def available_finished_products_factory(current_recipe_product_id=None):
    query = Product.query.filter_by(product_type='finished')
    subquery = db.session.query(Recipe.product_id).filter(Recipe.product_id.isnot(None))
    if current_recipe_product_id:
        subquery = subquery.filter(Recipe.product_id != current_recipe_product_id)
        query = query.filter(db.or_(Product.id == current_recipe_product_id, ~Product.id.in_(subquery)))
    else:
        query = query.filter(~Product.id.in_(subquery))
    return query.order_by(Product.name)

# --- FORMULAIRES UTILISATEUR ---
class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(message="Le nom d'utilisateur est requis."), Length(min=2, max=20, message="Le nom d'utilisateur doit contenir entre 2 et 20 caractères.")])
    email = StringField('Email', validators=[DataRequired(message="L'email est requis."), Email(message="Veuillez entrer une adresse email valide.")])
    password = PasswordField('Mot de passe', validators=[DataRequired(message="Le mot de passe est requis."), Length(min=6, message="Le mot de passe doit contenir au moins 6 caractères.")])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(message="La confirmation du mot de passe est requise."), EqualTo('password', message="Les mots de passe doivent correspondre.")])
    submit = SubmitField('S\'inscrire')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user: raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user: raise ValidationError('Cette adresse email est déjà utilisée.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="L'email est requis."), Email(message="Veuillez entrer une adresse email valide.")])
    password = PasswordField('Mot de passe', validators=[DataRequired(message="Le mot de passe est requis.")])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired(message="Le mot de passe actuel est requis.")])
    new_password = PasswordField('Nouveau mot de passe', validators=[DataRequired(message="Le nouveau mot de passe est requis."), Length(min=6, message="Le mot de passe doit contenir au moins 6 caractères.")])
    confirm_new_password = PasswordField('Confirmer le nouveau mot de passe', validators=[DataRequired(message="La confirmation du nouveau mot de passe est requise."), EqualTo('new_password', message="Les nouveaux mots de passe doivent correspondre.")])
    submit = SubmitField('Changer le mot de passe')
    def validate_current_password(self, current_password_field):
        if not current_user.is_authenticated or not check_password_hash(current_user.password_hash, current_password_field.data):
            raise ValidationError('Le mot de passe actuel est incorrect.')

# --- FORMULAIRES MÉTIER (Catégories, Produits, Stock) ---
class CategoryForm(FlaskForm):
    name = StringField('Nom de la catégorie', validators=[DataRequired(message="Le nom de la catégorie est requis."), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enregistrer la Catégorie')

    def __init__(self, formdata=None, obj=None, **kwargs): # Ajout pour gérer 'obj' correctement
        self.obj = obj
        super().__init__(formdata=formdata, obj=obj, **kwargs)

    def validate_name(self, name_field):
        category_query = Category.query.filter(Category.name == name_field.data)
        if hasattr(self, 'obj') and self.obj and self.obj.id: # Utiliser self.obj
             category_query = category_query.filter(Category.id != self.obj.id)
        if category_query.first():
            raise ValidationError('Une catégorie avec ce nom existe déjà.')

class ProductForm(FlaskForm):
    name = StringField('Nom du produit', validators=[DataRequired(message="Le nom du produit est requis."), Length(min=2, max=100)])
    product_type = SelectField('Type de produit', choices=[('finished', 'Produit Fini'), ('ingredient', 'Ingrédient')], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    price = DecimalField('Prix de vente (DA)', validators=[Optional(), NumberRange(min=0)], places=2)
    cost_price = DecimalField('Prix d\'achat / Coût (DA)', validators=[Optional(), NumberRange(min=0)], places=2)
    unit = SelectField('Unité de mesure', choices=[('Unité', 'Unité'), ('Kilogramme', 'Kilogramme (kg)'), ('Litre', 'Litre (L)'), ('Grammes', 'Grammes (g)'), ('Millilitre', 'Millilitre (ml)'), ('Paquet', 'Paquet'), ('Boîte', 'Boîte')], validators=[DataRequired()])
    sku = StringField('SKU (Référence)', validators=[Optional(), Length(max=50)])
    quantity_in_stock = IntegerField('Quantité en stock', validators=[DataRequired(message="La quantité est requise."), NumberRange(min=0)], default=0)
    category = QuerySelectField('Catégorie', query_factory=category_query_factory, get_label='name', allow_blank=False, validators=[DataRequired()])
    submit = SubmitField('Enregistrer le Produit')

    def __init__(self, formdata=None, obj=None, **kwargs): # Ajout pour gérer 'obj'
        self.obj = obj
        super().__init__(formdata=formdata, obj=obj, **kwargs)

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators): return False
        is_valid = True 
        if self.product_type.data == 'finished' and (self.price.data is None or self.price.data <= 0):
            self.price.errors.append('Le prix de vente est obligatoire et positif pour un produit fini.')
            is_valid = False
        return is_valid
    def validate_sku(self, sku_field):
        if sku_field.data:
            sku_query = Product.query.filter(Product.sku == sku_field.data)
            if hasattr(self, 'obj') and self.obj and self.obj.id: # Utiliser self.obj
                sku_query = sku_query.filter(Product.id != self.obj.id)
            if sku_query.first():
                raise ValidationError('Ce SKU est déjà utilisé.')

class StockAdjustmentForm(FlaskForm):
    product = QuerySelectField('Produit', query_factory=product_query_factory, get_label='name', allow_blank=False, validators=[DataRequired()])
    quantity = IntegerField('Quantité à ajuster (+/-)', validators=[DataRequired(message="La quantité d'ajustement est requise.")])
    reason = TextAreaField('Raison/Note', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Ajuster le Stock')

class QuickStockEntryForm(FlaskForm):
    product = QuerySelectField('Produit reçu', query_factory=product_query_factory, get_label='name', allow_blank=False, validators=[DataRequired()])
    quantity_received = IntegerField('Quantité reçue', validators=[DataRequired(), NumberRange(min=1, message="La quantité doit être au moins 1.")])
    submit = SubmitField('Enregistrer la Réception')

# --- FORMULAIRES DE COMMANDE ---
class OrderItemForm(FlaskForm):
    product = QuerySelectField('Produit', query_factory=finished_product_query_factory_for_orders, get_label='name', allow_blank=True, validators=[Optional()])
    quantity = IntegerField('Quantité', default=1, validators=[Optional(), NumberRange(min=1, message="La quantité doit être d'au moins 1.")])

class OrderForm(FlaskForm):
    order_type = SelectField('Type de Demande', choices=[('customer_order', 'Commande Client'), ('counter_production_request', 'Production pour Comptoir')], default='customer_order', validators=[DataRequired()])
    customer_name = StringField('Nom du client', validators=[Optional(), Length(min=2, max=100)])
    customer_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    customer_address = TextAreaField('Adresse de livraison', validators=[Optional(), Length(max=500)])
    delivery_option = SelectField('Option de Service', choices=[('pickup', 'Retrait en Magasin'), ('delivery', 'Livraison à Domicile')], default='pickup', validators=[DataRequired()])
    due_date = DateTimeLocalField('Date et Heure Prévue', validators=[DataRequired(message="La date et heure prévue sont requises.")], format='%Y-%m-%dT%H:%M')
    delivery_cost = DecimalField('Frais de Livraison (DA)', default=Decimal('0.00'), validators=[Optional(), NumberRange(min=0)], places=2)
    items = FieldList(FormField(OrderItemForm), min_entries=1, label="Articles Commandés")
    notes = TextAreaField('Notes pour la production/commande', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Enregistrer la Commande')
    def __init__(self, formdata=None, obj=None, **kwargs):
        self.obj = obj; self.edit_mode = obj is not None
        super().__init__(formdata=formdata, obj=obj, **kwargs)
        if self.edit_mode: self.submit.label.text = 'Modifier la Commande'
        else: self.submit.label.text = 'Créer la Commande'
        
    def validate(self, extra_validators=None):
        initial_super_validation = super().validate(extra_validators)
        is_custom_valid = True
        if self.order_type.data == 'customer_order':
            if not self.customer_name.data or not self.customer_name.data.strip(): self.customer_name.errors.append('Le nom du client est obligatoire.'); is_custom_valid = False
            if not self.customer_phone.data or not self.customer_phone.data.strip(): self.customer_phone.errors.append('Le téléphone du client est obligatoire.'); is_custom_valid = False
            if self.delivery_option.data == 'delivery' and (not self.customer_address.data or not self.customer_address.data.strip()): self.customer_address.errors.append('L\'adresse est obligatoire pour une livraison.'); is_custom_valid = False
            elif self.delivery_option.data == 'pickup' and self.delivery_cost.data and self.delivery_cost.data > 0: self.delivery_cost.errors.append('Pas de frais de livraison pour retrait.'); is_custom_valid = False
        elif self.order_type.data == 'counter_production_request' and self.delivery_cost.data and self.delivery_cost.data > 0: self.delivery_cost.errors.append('Pas de frais de livraison pour production comptoir.'); is_custom_valid = False
        valid_items_count = 0; has_item_errors = False
        if self.items.data:
            for i, item_form_data in enumerate(self.items.data):
                item_is_valid_for_count = True
                if not item_form_data.get('product'):
                    if i < len(self.items.entries): self.items.entries[i].form.product.errors.append("Sélectionnez un produit.")
                    item_is_valid_for_count = False; has_item_errors = True
                if not item_form_data.get('quantity') or int(item_form_data.get('quantity', 0)) <= 0:
                    if i < len(self.items.entries): self.items.entries[i].form.quantity.errors.append("Quantité positive requise.")
                    item_is_valid_for_count = False; has_item_errors = True
                if item_is_valid_for_count: valid_items_count += 1
        if valid_items_count == 0:
            if not self.items.errors: self.items.errors.append("Au moins un article valide est requis.")
            is_custom_valid = False
        return initial_super_validation and is_custom_valid and not has_item_errors

class OrderStatusForm(FlaskForm):
    status = SelectField('Nouveau Statut', choices=[('pending', 'En attente production'), ('ready_at_shop', 'Reçue au magasin'), ('out_for_delivery', 'En livraison client'), ('completed', 'Terminée'), ('awaiting_payment', 'Attente paiement livreur'), ('cancelled', 'Annulée')], validators=[DataRequired()])
    notes = TextAreaField('Notes additionnelles', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Mettre à Jour Statut')

# --- NOUVEAUX FORMULAIRES POUR LES RECETTES ---

class RecipeIngredientForm(FlaskForm):
    product = QuerySelectField('Ingrédient', query_factory=ingredient_products_factory, get_label='name', allow_blank=True, blank_text='--- Sélectionnez un ingrédient ---', validators=[Optional()])
    quantity_needed = DecimalField('Quantité nécessaire', validators=[Optional(), NumberRange(min=Decimal('0.001'), message="La quantité doit être positive.")], default=Decimal('1.000'), places=3, render_kw={'step': '0.001', 'placeholder': '1.000'})
    unit = StringField('Unité de mesure', validators=[Optional(), Length(max=50)], render_kw={'placeholder': 'g, kg, pièce...'})
    notes = StringField('Notes (optionnel)', validators=[Optional(), Length(max=255)], render_kw={'placeholder': 'Ex: finement haché'})

class RecipeForm(FlaskForm):
    name = StringField('Nom de la recette', validators=[DataRequired(message="Le nom de la recette est obligatoire."), Length(min=3, max=150, message="Le nom doit contenir entre 3 et 150 caractères.")], render_kw={'placeholder': 'Ex: Messemen Grand Taille'})
    description = TextAreaField('Description / Instructions', validators=[Optional(), Length(max=5000)], render_kw={'rows': 5, 'placeholder': 'Étapes de préparation...'})
    finished_product = QuerySelectField(
        'Produit fini associé à cette recette',
        query_factory=lambda: available_finished_products_factory(None), 
        get_label='name',
        allow_blank=False,
        validators=[DataRequired(message="Veuillez sélectionner le produit fini que cette recette produit.")],
        description="Sélectionnez le produit de votre catalogue qui sera fabriqué par cette recette."
    )
    yield_quantity = DecimalField('Quantité produite par la recette', validators=[DataRequired(message="Quantité produite requise."), NumberRange(min=Decimal('0.01'), message="Quantité positive requise.")], default=Decimal('1.0'), places=2, render_kw={'step': '0.01', 'placeholder': 'Ex: 112'})
    yield_unit = StringField('Unité de la quantité produite', validators=[DataRequired(message="L'unité de production est obligatoire."), Length(max=50)], default='pièces', render_kw={'placeholder': 'pièces, kg, L...'})
    preparation_time = IntegerField('Temps de préparation (minutes)', validators=[Optional(), NumberRange(min=0, message="Temps positif requis.")], render_kw={'placeholder': 'Ex: 30'})
    cooking_time = IntegerField('Temps de cuisson (minutes)', validators=[Optional(), NumberRange(min=0, message="Temps positif requis.")], render_kw={'placeholder': 'Ex: 45'})
    difficulty_level = SelectField('Niveau de difficulté', choices=[('', '--- Non spécifié ---'), ('Facile', 'Facile'), ('Moyen', 'Moyen'), ('Difficile', 'Difficile'), ('Expert', 'Expert')], validators=[Optional()], default='')
    ingredients = FieldList(FormField(RecipeIngredientForm), min_entries=1, label="Ingrédients")
    submit = SubmitField('Enregistrer la recette')

    def __init__(self, formdata=None, obj=None, **kwargs):
        self.obj = obj; self.edit_mode = obj is not None
        super().__init__(formdata=formdata, obj=obj, **kwargs)
        current_recipe_product_id = None
        if self.edit_mode and self.obj and self.obj.product_id:
            current_recipe_product_id = self.obj.product_id
            self.submit.label.text = 'Modifier la recette'
        self.finished_product.query_factory = lambda: available_finished_products_factory(current_recipe_product_id)

    def validate_name(self, field):
        query = Recipe.query.filter(Recipe.name == field.data)
        if self.edit_mode and self.obj: query = query.filter(Recipe.id != self.obj.id)
        if query.first(): raise ValidationError('Une recette avec ce nom existe déjà.')

    def validate_finished_product(self, field):
        if not field.data: return
        existing_recipe_for_product = Recipe.query.filter(Recipe.product_id == field.data.id).first()
        if existing_recipe_for_product and not (self.edit_mode and self.obj and existing_recipe_for_product.id == self.obj.id):
            raise ValidationError(f"Le produit fini '{field.data.name}' est déjà associé à la recette '{existing_recipe_for_product.name}'.")

    def validate_ingredients(self, field_list_ingredients): # Renommé pour clarté
        has_at_least_one_valid_ingredient = False
        all_active_rows_are_valid = True 
        product_ids_in_recipe = set()
        active_row_exists = False

        for i, ingredient_subform_entry in enumerate(field_list_ingredients):
            ingredient_form = ingredient_subform_entry.form
            is_active_row = bool(ingredient_form.product.data or ingredient_form.quantity_needed.data or (ingredient_form.unit.data and ingredient_form.unit.data.strip()))
            if is_active_row: active_row_exists = True

            if is_active_row:
                current_row_is_fully_valid = True
                if not ingredient_form.product.data:
                    ingredient_form.product.errors.append("Sélectionnez un ingrédient.")
                    current_row_is_fully_valid = False
                if not ingredient_form.quantity_needed.data or ingredient_form.quantity_needed.data <= Decimal('0'):
                    ingredient_form.quantity_needed.errors.append("Quantité positive requise.")
                    current_row_is_fully_valid = False
                if not ingredient_form.unit.data or not ingredient_form.unit.data.strip():
                    ingredient_form.unit.errors.append("Unité requise.")
                    current_row_is_fully_valid = False
                
                if current_row_is_fully_valid:
                    has_at_least_one_valid_ingredient = True
                    product_id = ingredient_form.product.data.id
                    if product_id in product_ids_in_recipe:
                        ingredient_form.product.errors.append('Ingrédient dupliqué.')
                        all_active_rows_are_valid = False 
                    else:
                        product_ids_in_recipe.add(product_id)
                else:
                    all_active_rows_are_valid = False 
        
        if active_row_exists and not has_at_least_one_valid_ingredient:
            field_list_ingredients.errors.append('La recette doit contenir au moins un ingrédient complet et valide.')
            return False

        # Si aucune ligne n'est active mais min_entries=1, et que la seule ligne est vide, on peut lever une erreur ici
        # Ou laisser les validateurs DataRequired des champs principaux de RecipeForm faire leur travail.
        # Si nous sommes ici, c'est que les champs principaux de RecipeForm sont valides.
        # On vérifie donc s'il y a au moins un ingrédient si des lignes existent.
        if not has_at_least_one_valid_ingredient and len(field_list_ingredients.entries)>0 and active_row_exists == False :
            # Ce cas se produit si min_entries=1 et que la seule ligne est complètement vide.
            # On peut ajouter une erreur ou considérer que c'est ok si on permet de sauvegarder une recette sans ingrédient au début.
            # Pour l'instant, exigeons au moins un ingrédient.
            field_list_ingredients.errors.append('Veuillez ajouter au moins un ingrédient à la recette.')
            return False


        return all_active_rows_are_valid # Retourne False s'il y a des erreurs dans les sous-formulaires actifs ou pas d'ingrédient valide