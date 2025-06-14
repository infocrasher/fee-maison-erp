from flask_wtf import FlaskForm
from wtforms import (
    StringField, 
    TextAreaField, 
    FieldList, 
    FormField, 
    SubmitField, 
    SelectField, 
    DecimalField,
    DateTimeField
)
from wtforms.validators import DataRequired, Optional, Length, Email
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product

# Cette fonction retourne les produits qui peuvent être vendus.
def get_sellable_products():
    return Product.query.filter_by(product_type='finished').order_by(Product.name).all()

# ✅ CORRECTION : Cette fonction définit comment afficher le nom du produit dans la liste déroulante.
# Elle inclut maintenant le nom, le prix et l'unité, exactement comme dans le module des recettes.
def get_product_label(product):
    price = product.price or 0.0
    return f"{product.name} ({price:.2f} DA / {product.unit})"

class OrderItemForm(FlaskForm):
    """
    Sous-formulaire pour un article dans une commande.
    """
    # ✅ CORRECTION : On utilise la fonction 'get_product_label' pour formater le texte de l'option.
    product = QuerySelectField(
        'Produit', 
        query_factory=get_sellable_products, 
        get_label=get_product_label, 
        allow_blank=True, 
        blank_text='-- Choisir un produit --',
        validators=[DataRequired("Veuillez sélectionner un produit.")]
    )
    quantity = DecimalField(
        'Quantité', 
        validators=[DataRequired("La quantité est requise.")], 
        default=1
    )

class OrderForm(FlaskForm):
    """
    Formulaire principal pour la création et l'édition de commandes.
    """
    order_type = SelectField(
        'Type de Commande', 
        choices=[
            ('in_store', 'Vente au Comptoir'), 
            ('customer_order', 'Commande Client')
        ], 
        validators=[DataRequired()]
    )

    # Champs client
    customer_name = StringField('Nom du client', validators=[Optional(), Length(max=100)])
    customer_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    customer_address = TextAreaField('Adresse de livraison', validators=[Optional(), Length(max=300)])
    
    # Options de service
    delivery_option = SelectField(
        'Option de service', 
        choices=[
            ('pickup', 'Retrait en magasin'), 
            ('delivery', 'Livraison à domicile')
        ], 
        validators=[Optional()]
    )
    
    due_date = DateTimeField(
        'Date/Heure de retrait/livraison', 
        format='%Y-%m-%dT%H:%M', 
        validators=[Optional()]
    )

    delivery_cost = DecimalField(
        'Coût de livraison', 
        validators=[Optional()], 
        default=0.0
    )

    items = FieldList(
        FormField(OrderItemForm), 
        min_entries=1
    )
    
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=5000)])
    submit = SubmitField('Enregistrer')

    # Logique de validation personnalisée
    def validate(self, extra_validators=None):
        initial_validation = super(OrderForm, self).validate(extra_validators)
        if not initial_validation:
            return False

        # Si c'est une commande client, le nom et le téléphone sont requis
        if self.order_type.data == 'customer_order':
            if not self.customer_name.data:
                self.customer_name.errors.append('Le nom du client est requis pour une commande client.')
                return False
            if not self.customer_phone.data:
                self.customer_phone.errors.append('Le téléphone du client est requis pour une commande client.')
                return False
            if not self.due_date.data:
                self.due_date.errors.append('La date de retrait/livraison est requise.')
                return False
        
        # Si la livraison est choisie, l'adresse est requise
        if self.order_type.data == 'customer_order' and self.delivery_option.data == 'delivery':
            if not self.customer_address.data:
                self.customer_address.errors.append("L'adresse de livraison est requise pour une livraison.")
                return False
        
        return True

class OrderStatusForm(FlaskForm):
    """
    Formulaire pour la mise à jour rapide du statut d'une commande.
    """
    status = SelectField(
        'Statut de la commande',
        choices=[
            ('pending', 'En attente'),
            ('in_progress', 'En préparation'),
            ('ready', 'Prête pour retrait/livraison'),
            ('completed', 'Terminée'),
            ('cancelled', 'Annulée')
        ],
        validators=[DataRequired()]
    )
    notes = TextAreaField('Ajouter une note (optionnel)', validators=[Optional()])
    submit = SubmitField('Mettre à jour le statut')