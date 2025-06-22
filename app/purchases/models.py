"""
Modèles pour la gestion des achats fournisseurs

Module: app/purchases/models.py

Auteur: ERP Fée Maison
"""

from extensions import db
from datetime import datetime, date
from enum import Enum
import uuid

class PurchaseStatus(Enum):
    """Statuts possibles d'un bon d'achat"""
    DRAFT = 'draft'                          # Brouillon
    REQUESTED = 'requested'                  # Demandé (en attente d'approbation)
    APPROVED = 'approved'                    # Approuvé
    ORDERED = 'ordered'                      # Commandé chez le fournisseur
    PARTIALLY_RECEIVED = 'partially_received' # Partiellement reçu
    RECEIVED = 'received'                    # Complètement reçu
    INVOICED = 'invoiced'                    # Facturé
    CANCELLED = 'cancelled'                  # Annulé

class PurchaseUrgency(Enum):
    """Niveaux d'urgence pour les achats"""
    LOW = 'low'                 # Faible
    NORMAL = 'normal'           # Normale
    HIGH = 'high'               # Haute  
    URGENT = 'urgent'           # Urgente

class Purchase(db.Model):
    """Bon d'achat principal avec gestion paiement simplifiée"""
    __tablename__ = 'purchases'
    
    # Identification
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    
    # Informations fournisseur
    supplier_name = db.Column(db.String(200), nullable=False)
    supplier_contact = db.Column(db.String(100))
    supplier_phone = db.Column(db.String(20))
    supplier_email = db.Column(db.String(120))
    supplier_address = db.Column(db.Text)
    
    # État et urgence
    status = db.Column(db.Enum(PurchaseStatus), nullable=False, default=PurchaseStatus.DRAFT)
    urgency = db.Column(db.Enum(PurchaseUrgency), nullable=False, default=PurchaseUrgency.NORMAL)
    
    # Responsables
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Dates importantes
    requested_date = db.Column(db.DateTime, nullable=False)
    approved_date = db.Column(db.DateTime)
    expected_delivery_date = db.Column(db.DateTime)
    received_date = db.Column(db.DateTime)
    
    # ✅ NOUVEAUX CHAMPS : Gestion paiement simplifiée
    is_paid = db.Column(db.Boolean, default=False, nullable=True)  # Nullable pour éviter l'erreur
    payment_date = db.Column(db.Date, nullable=True)  # Date paiement si payé

    # Montants
    subtotal_amount = db.Column(db.Numeric(10, 2), default=0.0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.0)
    shipping_cost = db.Column(db.Numeric(10, 2), default=0.0)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Informations complémentaires
    notes = db.Column(db.Text)                    # Notes visibles du fournisseur
    internal_notes = db.Column(db.Text)           # Notes internes
    terms_conditions = db.Column(db.Text)         # Conditions particulières
    payment_terms = db.Column(db.String(100))     # Conditions de paiement
    default_stock_location = db.Column(db.String(50), default='ingredients_magasin')
    
    # Horodatage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='requested_purchases', lazy=True)
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_purchases', lazy=True)
    received_by = db.relationship('User', foreign_keys=[received_by_id], backref='received_purchases', lazy=True)
    
    def __init__(self, **kwargs):
        super(Purchase, self).__init__(**kwargs)
        if not self.reference:
            self.reference = self.generate_reference()
    
    def generate_reference(self):
        """Génère une référence unique pour le bon d'achat"""
        year = datetime.now().year
        random_part = str(uuid.uuid4())[:8].upper()
        return f'BA{year}-{random_part}'
    
    def __repr__(self):
        return f'<Purchase {self.reference}: {self.supplier_name}>'
    
    def calculate_totals(self):
        """Calcule les totaux du bon d'achat"""
        self.subtotal_amount = sum(item.line_total_with_discount for item in self.items)
        self.total_amount = float(self.subtotal_amount) + float(self.tax_amount or 0) + float(self.shipping_cost or 0)
    
    def can_be_modified(self):
        """Vérifie si le bon d'achat peut être modifié"""
        return self.status in [PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED]
    
    def can_be_approved(self):
        """Vérifie si le bon d'achat peut être approuvé"""
        return self.status == PurchaseStatus.REQUESTED
    
    def can_be_ordered(self):
        """Vérifie si le bon d'achat peut être commandé"""
        return self.status == PurchaseStatus.APPROVED
    
    def is_overdue(self):
        """Vérifie si le bon d'achat est en retard"""
        if not self.expected_delivery_date:
            return False
        return (self.expected_delivery_date < datetime.utcnow() and 
                self.status not in [PurchaseStatus.RECEIVED, PurchaseStatus.INVOICED, PurchaseStatus.CANCELLED])
    
    # ✅ NOUVELLES PROPRIÉTÉS : Gestion affichage paiement
    @property
    def payment_status_display(self):
        """Affichage du statut de paiement"""
        if self.is_paid:
            if self.payment_date:
                return f"✅ Payé le {self.payment_date.strftime('%d/%m/%Y')}"
            else:
                return "✅ Payé (date inconnue)"
        else:
            return "⏳ Non payé"
    
    @property 
    def payment_badge_class(self):
        """Classe CSS pour le badge de statut paiement"""
        return "bg-success" if self.is_paid else "bg-warning"
    
    @property
    def status_label(self):
        """Label français du statut"""
        status_labels = {
            PurchaseStatus.DRAFT: 'Brouillon',
            PurchaseStatus.REQUESTED: 'Demandé',
            PurchaseStatus.APPROVED: 'Approuvé',
            PurchaseStatus.ORDERED: 'Commandé',
            PurchaseStatus.PARTIALLY_RECEIVED: 'Partiellement reçu',
            PurchaseStatus.RECEIVED: 'Reçu',
            PurchaseStatus.INVOICED: 'Facturé',
            PurchaseStatus.CANCELLED: 'Annulé'
        }
        return status_labels.get(self.status, self.status.value)
    
    @property
    def urgency_label(self):
        """Label français de l'urgence"""
        urgency_labels = {
            PurchaseUrgency.LOW: 'Faible',
            PurchaseUrgency.NORMAL: 'Normale',
            PurchaseUrgency.HIGH: 'Haute',
            PurchaseUrgency.URGENT: 'Urgente'
        }
        return urgency_labels.get(self.urgency, self.urgency.value)

class PurchaseItem(db.Model):
    """Ligne d'article dans un bon d'achat avec support des unités prédéfinies"""
    __tablename__ = 'purchase_items'
    
    # Identification
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Quantités et prix (en unité de base pour calculs)
    quantity_ordered = db.Column(db.Numeric(10, 3), nullable=False)  # En unité de base (g, ml)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)        # Prix par unité de base
    discount_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    
    # Champs pour gestion unités de conditionnement
    original_quantity = db.Column(db.Numeric(10, 3), nullable=True)     # 2 (pour 2 × 25kg)
    original_unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    original_unit_price = db.Column(db.Numeric(10, 2), nullable=True)   # 1500 DA/sac de 25kg
    
    # Informations de réception
    quantity_received = db.Column(db.Numeric(10, 3), default=0.0)
    
    # Localisation et description
    stock_location = db.Column(db.String(50), nullable=False, default='ingredients_magasin')
    description_override = db.Column(db.String(255))
    supplier_reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Horodatage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    purchase = db.relationship('Purchase', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))
    product = db.relationship('Product', backref='purchase_items', lazy=True)
    original_unit = db.relationship('Unit', backref='purchase_items', lazy=True)
    
    def __repr__(self):
        return f'<PurchaseItem {self.id}: {self.product.name if self.product else "N/A"}>'
    
    @property
    def line_total(self):
        """Total de la ligne (quantité × prix unitaire)"""
        return float(self.quantity_ordered) * float(self.unit_price)
    
    @property
    def line_total_with_discount(self):
        """Total avec remise appliquée"""
        total = self.line_total
        if self.discount_percentage:
            total = total * (1 - float(self.discount_percentage) / 100)
        return total
    
    @property
    def original_line_total(self):
        """Total basé sur la quantité et prix originaux"""
        if self.original_quantity and self.original_unit_price:
            return float(self.original_quantity) * float(self.original_unit_price)
        return self.line_total
    
    @property
    def display_quantity(self):
        """Affichage lisible de la quantité avec unité originale"""
        if self.original_unit and self.original_quantity:
            return f"{self.original_quantity} × {self.original_unit.name}"
        else:
            return f"{self.quantity_ordered}"
    
    @property
    def display_unit_price(self):
        """Affichage du prix unitaire original"""
        if self.original_unit_price and self.original_unit:
            return f"{self.original_unit_price} DA/{self.original_unit.name}"
        else:
            return f"{self.unit_price} DA/unité de base"
    
    @property
    def display_total_base_quantity(self):
        """Quantité totale en unité de base pour vérification"""
        if self.original_unit:
            base_unit = self.original_unit.base_unit
            return f"{self.quantity_ordered}{base_unit}"
        return f"{self.quantity_ordered}"
    
    @property
    def is_fully_received(self):
        """Vérifie si l'article est complètement reçu"""
        return float(self.quantity_received) >= float(self.quantity_ordered)
    
    @property
    def remaining_quantity(self):
        """Quantité restante à recevoir"""
        return max(0, float(self.quantity_ordered) - float(self.quantity_received))
    
    def get_conversion_info(self):
        """Informations de conversion pour debug/vérification"""
        if self.original_unit:
            return {
                'original': f"{self.original_quantity} × {self.original_unit.name}",
                'converted': f"{self.quantity_ordered}{self.original_unit.base_unit}",
                'factor': self.original_unit.conversion_factor,
                'price_original': f"{self.original_unit_price} DA/{self.original_unit.name}",
                'price_base': f"{self.unit_price} DA/{self.original_unit.base_unit}"
            }
        return None

    @property
    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet, sérialisable en JSON."""
        return {
            'id': self.id,
            'purchase_id': self.purchase_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Produit inconnu',
            'quantity_ordered': float(self.quantity_ordered),
            'unit_price': float(self.unit_price),
            'discount_percentage': float(self.discount_percentage),
            'original_quantity': float(self.original_quantity) if self.original_quantity else None,
            'original_unit_id': self.original_unit_id,
            'original_unit_price': float(self.original_unit_price) if self.original_unit_price else None,
            'stock_location': self.stock_location,
            'description_override': self.description_override,
        }