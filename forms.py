# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, DecimalField, IntegerField, SelectField
from wtforms import FieldList, FormField 
from wtforms.fields import DateTimeLocalField 
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_login import current_user
from werkzeug.security import check_password_hash
from decimal import Decimal

# Assurez-vous que tous les modèles nécessaires sont importés
from models import User, Category, Product, Order, OrderItem 

# --- FACTORIES POUR QUERYSELECTFIELD ---
def category_query_factory():
    return Category.query.order_by(Category.name)

def product_query_factory():
    return Product.query.order_by(Product.name)

def finished_product_query_factory(): 
    return Product.query.filter_by(product_type='finished').order_by(Product.name)
# --- FIN FACTORIES ---

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message="Le nom d'utilisateur est requis."),
        Length(min=2, max=20, message="Le nom d'utilisateur doit contenir entre 2 et 20 caractères.")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="L'email est requis."),
        Email(message="Veuillez entrer une adresse email valide.")
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message="Le mot de passe est requis."),
        Length(min=6, message="Le mot de passe doit contenir au moins 6 caractères.")
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(message="La confirmation du mot de passe est requise."),
        EqualTo('password', message="Les mots de passe doivent correspondre.")
    ])
    submit = SubmitField('S\'inscrire')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris. Veuillez en choisir un autre.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cette adresse email est déjà utilisée. Veuillez en choisir une autre.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="L'email est requis."),
        Email(message="Veuillez entrer une adresse email valide.")
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message="Le mot de passe est requis.")
    ])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[
        DataRequired(message="Le mot de passe actuel est requis.")
    ])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(message="Le nouveau mot de passe est requis."),
        Length(min=6, message="Le mot de passe doit contenir au moins 6 caractères.")
    ])
    confirm_new_password = PasswordField('Confirmer le nouveau mot de passe', validators=[
        DataRequired(message="La confirmation du nouveau mot de passe est requise."),
        EqualTo('new_password', message="Les nouveaux mots de passe doivent correspondre.")
    ])
    submit = SubmitField('Changer le mot de passe')

    def validate_current_password(self, current_password_field):
        if not current_user.is_authenticated:
            raise ValidationError('Utilisateur non authentifié.')
        if not check_password_hash(current_user.password_hash, current_password_field.data):
            raise ValidationError('Le mot de passe actuel est incorrect.')

class CategoryForm(FlaskForm):
    name = StringField('Nom de la catégorie', validators=[
        DataRequired(message="Le nom de la catégorie est requis."),
        Length(min=2, max=50, message="Le nom doit contenir entre 2 et 50 caractères.")
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enregistrer la Catégorie')

    def validate_name(self, name_field):
        category_query = Category.query.filter(Category.name == name_field.data)
        if hasattr(self, '_obj') and self._obj and self._obj.id:
             category_query = category_query.filter(Category.id != self._obj.id)
        existing_category = category_query.first()
        if existing_category:
            raise ValidationError('Une catégorie avec ce nom existe déjà.')

class ProductForm(FlaskForm):
    name = StringField('Nom du produit', validators=[
        DataRequired(message="Le nom du produit est requis."),
        Length(min=2, max=100, message="Le nom doit contenir entre 2 et 100 caractères.")
    ])
    product_type = SelectField('Type de produit', 
        choices=[('finished', 'Produit Fini (pour la vente)'), ('ingredient', 'Ingrédient / Matière Première')],
        validators=[DataRequired(message="Le type de produit est requis.")]
    )
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    price = DecimalField('Prix de vente (DA)', validators=[Optional(), NumberRange(min=0, message="Le prix doit être positif ou nul.")], places=2)
    cost_price = DecimalField('Prix d\'achat / Coût (DA)', validators=[Optional(), NumberRange(min=0, message="Le coût doit être positif ou nul.")], places=2)
    unit = SelectField('Unité de mesure', 
        choices=[
            ('Unité', 'Unité'), ('Kilogramme', 'Kilogramme (kg)'), ('Litre', 'Litre (L)'),
            ('Grammes', 'Grammes (g)'), ('Millilitre', 'Millilitre (ml)'),
            ('Paquet', 'Paquet'), ('Boîte', 'Boîte')
        ],
        validators=[DataRequired(message="L'unité de mesure est requise.")]
    )
    sku = StringField('SKU (Référence)', validators=[Optional(), Length(max=50)])
    quantity_in_stock = IntegerField('Quantité en stock initiale', validators=[
        DataRequired(message="La quantité est requise."),
        NumberRange(min=0, message="La quantité ne peut être négative.")
    ], default=0)
    category = QuerySelectField('Catégorie',
        query_factory=category_query_factory, 
        get_label='name',
        allow_blank=False,
        validators=[DataRequired(message="Veuillez sélectionner une catégorie.")]
    )
    submit = SubmitField('Enregistrer le Produit')

    def validate(self, extra_validators=None):
        initial_validation = super(ProductForm, self).validate(extra_validators)
        if not initial_validation: return False
        is_valid = True 
        if self.product_type.data == 'finished':
            if self.price.data is None or self.price.data <= 0:
                self.price.errors.append('Le prix de vente est obligatoire et doit être positif pour un produit fini.')
                is_valid = False
        if self.product_type.data == 'ingredient':
            if self.cost_price.data is None or self.cost_price.data <= 0:
                self.cost_price.errors.append('Le prix d\'achat/coût est obligatoire et doit être positif pour un ingrédient.')
                is_valid = False
        return is_valid

    def validate_sku(self, sku_field):
        if sku_field.data:
            sku_query = Product.query.filter(Product.sku == sku_field.data)
            if hasattr(self, '_obj') and self._obj and self._obj.id: 
                sku_query = sku_query.filter(Product.id != self._obj.id)
            if sku_query.first():
                raise ValidationError('Ce SKU est déjà utilisé par un autre produit.')

class StockAdjustmentForm(FlaskForm):
    product = QuerySelectField('Produit',query_factory=product_query_factory,get_label='name',allow_blank=False,validators=[DataRequired()])
    quantity = IntegerField('Quantité à ajuster', validators=[DataRequired(message="La quantité d'ajustement est requise.")])
    reason = TextAreaField('Raison/Note', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Ajuster le Stock')

class QuickStockEntryForm(FlaskForm):
    product = QuerySelectField('Produit reçu',query_factory=product_query_factory,get_label='name',allow_blank=False,validators=[DataRequired()])
    quantity_received = IntegerField('Quantité reçue', validators=[DataRequired(),NumberRange(min=1, message="La quantité doit être au moins 1.")])
    submit = SubmitField('Enregistrer la Réception')

class OrderItemForm(FlaskForm):
    """Sous-formulaire pour UN article de commande."""
    product = QuerySelectField('Produit',
        query_factory=finished_product_query_factory, 
        get_label='name',
        allow_blank=True, # Important pour que "Sélectionnez un produit..." soit une option valide (vide)
        validators=[Optional()] # La validation principale se fait dans OrderForm
    )
    quantity = IntegerField('Quantité',
        default=1,
        validators=[Optional(), NumberRange(min=1, message="La quantité doit être d'au moins 1.")]
    )

class OrderForm(FlaskForm):
    order_type = SelectField('Type de Demande',
        choices=[('customer_order', 'Commande Client'), ('counter_production_request', 'Production pour Comptoir')],
        default='customer_order', validators=[DataRequired(message="Le type de demande est requis.")]
    )
    customer_name = StringField('Nom du client', validators=[Optional(), Length(min=2, max=100)])
    customer_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    customer_address = TextAreaField('Adresse de livraison', validators=[Optional(), Length(max=500)])
    
    delivery_option = SelectField('Option de Service',
        choices=[('pickup', 'Retrait en Magasin'), ('delivery', 'Livraison à Domicile')],
        default='pickup', validators=[DataRequired(message="Veuillez choisir une option de service.")]
    )
    # due_date est DataRequired car l'heure est maintenant toujours attendue
    due_date = DateTimeLocalField('Date et Heure Prévue', validators=[DataRequired(message="La date et heure prévue sont requises.")], format='%Y-%m-%dT%H:%M')
    delivery_cost = DecimalField('Frais de Livraison (DA)', default=Decimal('0.00'), validators=[Optional(), NumberRange(min=0)], places=2)
    
    items = FieldList(FormField(OrderItemForm), min_entries=1, label="Articles Commandés")
    
    notes = TextAreaField('Notes pour la production/commande', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Enregistrer la Commande')

    def __init__(self, *args, **kwargs):
        self.edit_mode = kwargs.pop('edit_mode', False) # Ne pas passer edit_mode à super()
        super().__init__(*args, **kwargs)
        if self.edit_mode:
            self.submit.label.text = 'Modifier la Commande'
        else:
            self.submit.label.text = 'Créer la Commande'

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators): return False
        is_form_valid = True
        
        # Validation des champs client si c'est une commande client
        if self.order_type.data == 'customer_order':
            if not self.customer_name.data or not self.customer_name.data.strip():
                self.customer_name.errors.append('Le nom du client est obligatoire pour une commande client.')
                is_form_valid = False
            if not self.customer_phone.data or not self.customer_phone.data.strip():
                self.customer_phone.errors.append('Le téléphone du client est obligatoire pour une commande client.')
                is_form_valid = False
            if self.delivery_option.data == 'delivery':
                if not self.customer_address.data or not self.customer_address.data.strip():
                    self.customer_address.errors.append('L\'adresse est obligatoire pour une livraison à domicile.')
                    is_form_valid = False
                # Frais de livraison peuvent être 0 pour livraison gratuite
            elif self.delivery_option.data == 'pickup':
                if self.delivery_cost.data and self.delivery_cost.data > 0:
                    self.delivery_cost.errors.append('Les frais de livraison ne s\'appliquent pas au retrait en magasin.')
                    is_form_valid = False
        elif self.order_type.data == 'counter_production_request':
            # Pour production comptoir, les frais de livraison doivent être nuls
            if self.delivery_cost.data and self.delivery_cost.data > 0:
                self.delivery_cost.errors.append('Les frais de livraison ne s\'appliquent pas à une production pour comptoir.')
                is_form_valid = False
        
        # Valider qu'il y a au moins un item valide
        valid_items_count = 0
        if self.items.data:
            for i, item_form_data in enumerate(self.items.data):
                item_is_valid_for_count = True
                if not item_form_data.get('product'):
                    # Ajouter l'erreur au champ product du sous-formulaire si possible
                    if i < len(self.items.entries) and self.items.entries[i].form.product:
                         self.items.entries[i].form.product.errors.append("Veuillez sélectionner un produit.")
                    item_is_valid_for_count = False
                    is_form_valid = False 
                if not item_form_data.get('quantity') or int(item_form_data.get('quantity', 0)) <= 0:
                    if i < len(self.items.entries) and self.items.entries[i].form.quantity:
                        self.items.entries[i].form.quantity.errors.append("La quantité doit être positive.")
                    item_is_valid_for_count = False
                    is_form_valid = False
                
                if item_is_valid_for_count:
                    valid_items_count += 1
        
        if valid_items_count == 0:
            # Ajouter une erreur globale au champ items si possible, ou une erreur non-field
            # WTForms ne gère pas bien les erreurs globales pour FieldList directement affichables
            # Il est préférable de flasher un message ou d'ajouter à _form_errors si géré dans le template
            # Pour l'instant, on marque le formulaire comme invalide. La route peut flasher.
            if not self.items.errors: # S'il n'y a pas déjà des erreurs plus spécifiques
                 self.items.errors.append("La commande doit contenir au moins un article valide (produit et quantité).")
            is_form_valid = False

        return is_form_valid

class OrderStatusForm(FlaskForm):
    status = SelectField('Nouveau Statut',
        choices=[
            ('pending', 'En attente production'), ('ready_at_shop', 'Reçue au magasin'), 
            ('out_for_delivery', 'En livraison client'), ('completed', 'Terminée'),
            ('awaiting_payment', 'Attente paiement livreur'), ('cancelled', 'Annulée')
        ], 
        validators=[DataRequired(message="Veuillez sélectionner un nouveau statut.")]
    )
    notes = TextAreaField('Notes additionnelles (optionnel)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Mettre à Jour Statut')