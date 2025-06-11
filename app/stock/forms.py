from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Product

# Factory pour lister tous les produits
def all_product_query_factory():
    return Product.query.order_by(Product.name)

class StockAdjustmentForm(FlaskForm):
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    # Permet les ajustements positifs et négatifs
    quantity = FloatField('Changement de quantité (+/-)', validators=[DataRequired()])
    reason = StringField('Raison', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Ajuster le stock')

class QuickStockEntryForm(FlaskForm):
    product = QuerySelectField('Produit', query_factory=all_product_query_factory, get_label='name', allow_blank=False)
    quantity_received = FloatField('Quantité reçue', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Ajouter au stock')