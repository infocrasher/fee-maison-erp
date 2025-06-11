from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, FloatField, IntegerField, 
                     FieldList, FormField, DateTimeField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product

# Cette fonction est nécessaire pour le QuerySelectField dans OrderItemForm
def finished_product_query_factory_for_orders():
    return Product.query.filter_by(product_type='finished').order_by(Product.name)

class OrderItemForm(FlaskForm):
    # On utilise allow_blank=True car la validation se fera au niveau du formulaire parent
    product = QuerySelectField('Produit', query_factory=finished_product_query_factory_for_orders, get_label='name', allow_blank=True)
    quantity = IntegerField('Qté', validators=[Optional(), NumberRange(min=1)])

class OrderForm(FlaskForm):
    order_type = SelectField('Type', choices=[('customer_order', 'Demande Client'), ('counter_production_request', 'Prod. Comptoir')], default='customer_order')
    customer_name = StringField('Nom du client', validators=[Optional(), Length(max=200)])
    customer_phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    customer_address = TextAreaField('Adresse', validators=[Optional()])
    # Le format doit correspondre à celui attendu par les navigateurs pour datetime-local
    due_date = DateTimeField("Date de livraison/retrait", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    delivery_option = SelectField('Livraison', choices=[('pickup', 'Retrait'), ('delivery', 'Livraison')], default='pickup')
    delivery_cost = FloatField('Coût de livraison (€)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    items = FieldList(FormField(OrderItemForm), min_entries=1, label="Articles")
    submit = SubmitField('Enregistrer la commande')

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