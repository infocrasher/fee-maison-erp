from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, FloatField, IntegerField,
                     FieldList, FormField, DateTimeField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product

def finished_product_query_factory_for_orders():
    return Product.query.filter_by(product_type='finished').order_by(Product.name)

class OrderItemForm(FlaskForm):
    class Meta:
        csrf = False  # Désactive CSRF pour les sous-formulaires dynamiques
    product = QuerySelectField('Produit', query_factory=finished_product_query_factory_for_orders, get_label='name', allow_blank=True)
    quantity = IntegerField('Qté', validators=[Optional(), NumberRange(min=1)])

class OrderForm(FlaskForm):
    order_type = SelectField('Type', choices=[('customer_order', 'Demande Client'), ('counter_production_request', 'Prod. Comptoir')], default='customer_order')
    customer_name = StringField('Nom du client', validators=[Optional(), Length(max=200)])
    customer_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    customer_address = TextAreaField('Adresse', validators=[Optional()])
    due_date = DateTimeField("Date de livraison/retrait", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    delivery_option = SelectField('Livraison', choices=[('pickup', 'Retrait'), ('delivery', 'Livraison')], default='pickup')
    delivery_cost = FloatField('Coût de livraison (DA)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    items = FieldList(FormField(OrderItemForm), min_entries=1, label="Articles")
    submit = SubmitField('Enregistrer la commande')

    def validate(self, extra_validators=None):
        rv = super().validate(extra_validators)
        if not rv:
            return False

        # Validation conditionnelle
        if self.order_type.data == 'customer_order':
            if not self.customer_name.data:
                self.customer_name.errors.append("Champ requis pour une commande client.")
                return False
            if not self.customer_phone.data:
                self.customer_phone.errors.append("Champ requis pour une commande client.")
                return False
            if self.delivery_option.data == 'delivery' and not self.customer_address.data:
                self.customer_address.errors.append("Adresse obligatoire en cas de livraison.")
                return False
        return True

class OrderStatusForm(FlaskForm):
    status = SelectField('Nouveau Statut', choices=[
        ('pending', 'En attente'),
        ('ready_at_shop', 'Prête en boutique'),
        ('out_for_delivery', 'En livraison'),
        ('completed', 'Terminée'),
        ('awaiting_payment', 'En attente de paiement'),
        ('cancelled', 'Annulée')
    ], validators=[DataRequired()])
    notes = TextAreaField('Ajouter une note (optionnel)', validators=[Optional()])
    submit = SubmitField('Mettre à jour le statut')