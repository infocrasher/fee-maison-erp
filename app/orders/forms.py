from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    FieldList,
    FormField,
    SubmitField,
    SelectField,
    DecimalField,
    DateTimeField,
    DateField
)
from wtforms.validators import DataRequired, Optional, Length
from models import Product

def get_sellable_products():
    return Product.query.filter_by(product_type='finished').order_by(Product.name).all()

class OrderItemForm(FlaskForm):
    class Meta:
        csrf = False
    
    product = SelectField(
        'Produit',
        choices=[('', '-- Choisir un produit --')],
        validators=[DataRequired("Veuillez sélectionner un produit.")]
    )
    
    quantity = DecimalField(
        'Quantité',
        validators=[DataRequired("La quantité est requise.")],
        default=1
    )

class CustomerOrderItemForm(FlaskForm):
    class Meta:
        csrf = False
    
    product = SelectField(
        'Produit',
        choices=[('', '-- Choisir un produit --')],
        validators=[DataRequired("Veuillez sélectionner un produit.")]
    )
    
    quantity = DecimalField(
        'Quantité',
        validators=[DataRequired("La quantité est requise.")],
        default=1
    )

class ProductionOrderItemForm(FlaskForm):
    class Meta:
        csrf = False
    
    product = SelectField(
        'Produit',
        choices=[('', '-- Choisir un produit --')],
        validators=[DataRequired("Veuillez sélectionner un produit.")]
    )
    
    quantity = DecimalField(
        'Quantité',
        validators=[DataRequired("La quantité est requise.")],
        default=1
    )

class OrderForm(FlaskForm):
    order_type = SelectField(
        'Type de Commande',
        choices=[
            ('in_store', 'Vente au Comptoir'),
            ('customer_order', 'Commande Client')
        ],
        validators=[DataRequired()]
    )

    customer_name = StringField('Nom du client', validators=[Optional(), Length(max=100)])
    customer_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    customer_address = TextAreaField('Adresse de livraison', validators=[Optional(), Length(max=300)])
    
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

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        products = get_sellable_products()
        product_choices = [('', '-- Choisir un produit --')]
        for product in products:
            price = product.price or 0.0
            label = f"{product.name} ({price:.2f} DA / {product.unit})"
            product_choices.append((str(product.id), label))
        
        for item_form in self.items:
            item_form.product.choices = product_choices

    def validate(self, extra_validators=None):
        initial_validation = super(OrderForm, self).validate(extra_validators)
        if not initial_validation:
            return False

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

        if self.order_type.data == 'customer_order' and self.delivery_option.data == 'delivery':
            if not self.customer_address.data:
                self.customer_address.errors.append("L'adresse de livraison est requise pour une livraison.")
                return False

        return True

class CustomerOrderForm(FlaskForm):
    customer_name = StringField('Nom du client', validators=[DataRequired("Le nom du client est requis."), Length(max=100)])
    customer_phone = StringField('Téléphone', validators=[DataRequired("Le téléphone est requis."), Length(max=20)])
    customer_address = TextAreaField('Adresse de livraison', validators=[Optional(), Length(max=300)])
    
    delivery_option = SelectField(
        'Option de retrait',
        choices=[
            ('pickup', 'Retrait en magasin'),
            ('delivery', 'Livraison à domicile')
        ],
        validators=[DataRequired()]
    )

    due_date = DateTimeField(
        'Date/Heure de retrait/livraison',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired("La date est requise.")]
    )

    delivery_cost = DecimalField(
        'Coût de livraison (DA)',
        validators=[Optional()],
        default=0.0
    )

    payment_status = SelectField(
        'Statut paiement',
        choices=[
            ('pending', 'En attente'),
            ('partial', 'Acompte versé'),
            ('paid', 'Payé intégralement')
        ],
        default='pending'
    )

    advance_payment = DecimalField(
        'Acompte versé (DA)',
        validators=[Optional()],
        default=0.0
    )

    items = FieldList(
        FormField(CustomerOrderItemForm),
        min_entries=1
    )

    notes = TextAreaField('Notes spéciales', validators=[Optional(), Length(max=5000)])
    submit = SubmitField('Enregistrer la commande')

    def __init__(self, *args, **kwargs):
        super(CustomerOrderForm, self).__init__(*args, **kwargs)
        products = get_sellable_products()
        product_choices = [('', '-- Choisir un produit --')]
        for product in products:
            price = product.price or 0.0
            label = f"{product.name} ({price:.2f} DA / {product.unit})"
            product_choices.append((str(product.id), label))
        
        for item_form in self.items:
            item_form.product.choices = product_choices

    def validate(self, extra_validators=None):
        initial_validation = super(CustomerOrderForm, self).validate(extra_validators)
        if not initial_validation:
            return False

        if self.delivery_option.data == 'delivery' and not self.customer_address.data:
            self.customer_address.errors.append("L'adresse de livraison est requise pour une livraison.")
            return False

        return True

class ProductionOrderForm(FlaskForm):
    production_date = DateField(
        'Date de production souhaitée',
        validators=[Optional()]
    )
    
    priority = SelectField(
        'Priorité',
        choices=[
            ('normal', 'Normale'),
            ('urgent', 'Urgente'),
            ('low', 'Faible')
        ],
        default='normal'
    )

    production_location = SelectField(
        'Lieu de production',
        choices=[
            ('main_kitchen', 'Cuisine Local'),
            ('store_counter', 'Cuisine Magasin')
        ],
        default='main_kitchen'
    )

    items = FieldList(
        FormField(ProductionOrderItemForm),
        min_entries=1
    )

    production_notes = TextAreaField('Instructions de production', validators=[Optional(), Length(max=5000)])
    submit = SubmitField('Créer ordre de production')

    def __init__(self, *args, **kwargs):
        super(ProductionOrderForm, self).__init__(*args, **kwargs)
        products = get_sellable_products()
        product_choices = [('', '-- Choisir un produit --')]
        for product in products:
            label = f"{product.name} (Unité: {product.unit})"
            product_choices.append((str(product.id), label))
        
        for item_form in self.items:
            item_form.product.choices = product_choices

class OrderStatusForm(FlaskForm):
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
