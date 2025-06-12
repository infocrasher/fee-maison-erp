# Fichier: app/stock/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from extensions import db
from models import Product
from .forms import StockAdjustmentForm, QuickStockEntryForm
from decorators import admin_required
from sqlalchemy import func

stock = Blueprint('stock', __name__)

@stock.route('/overview')
@login_required
@admin_required
def overview():
    low_stock_threshold = current_app.config.get('LOW_STOCK_THRESHOLD', 5)
    low_stock_products = Product.query.filter(Product.quantity_in_stock != None, Product.quantity_in_stock > 0, Product.quantity_in_stock < low_stock_threshold).order_by(Product.quantity_in_stock).all()
    out_of_stock_products = Product.query.filter((Product.quantity_in_stock == 0) | (Product.quantity_in_stock == None)).order_by(Product.name).all()
    return render_template('stock/stock_overview.html', title="Vue d'ensemble du Stock", low_stock_products=low_stock_products, out_of_stock_products=out_of_stock_products)

@stock.route('/quick_entry', methods=['GET', 'POST'])
@login_required
@admin_required
def quick_entry():
    form = QuickStockEntryForm()
    if form.validate_on_submit():
        product_obj = form.product.data
        quantity_received = form.quantity_received.data
        product_obj.quantity_in_stock = (product_obj.quantity_in_stock or 0) + quantity_received
        db.session.commit()
        flash(f'Stock pour "{product_obj.name}" mis à jour : {product_obj.quantity_in_stock}.', 'success')
        return redirect(url_for('stock.quick_entry'))
    return render_template('stock/quick_stock_entry.html', form=form, title='Réception Rapide')

@stock.route('/adjustment', methods=['GET', 'POST'])
@login_required
@admin_required
def adjustment():
    form = StockAdjustmentForm()
    if form.validate_on_submit():
        product_obj = form.product.data
        quantity_change = form.quantity.data
        old_stock = product_obj.quantity_in_stock or 0
        new_stock = old_stock + quantity_change
        if new_stock < 0:
            flash(f'Le stock de "{product_obj.name}" ne peut pas devenir négatif.', 'danger')
        else:
            product_obj.quantity_in_stock = new_stock
            db.session.commit()
            flash(f'Stock de "{product_obj.name}" ajusté à {new_stock}.', 'success')
            return redirect(url_for('stock.adjustment'))
    return render_template('stock/stock_adjustment_form.html', form=form, title='Ajustement de Stock')