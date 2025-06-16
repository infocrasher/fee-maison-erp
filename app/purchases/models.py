"""
Modèles pour la gestion des achats fournisseurs
Module: app/purchases/models.py
Auteur: ERP Fée Maison
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from extensions import db
from sqlalchemy import and_

class PurchaseStatus(Enum):
    """Statuts des bons d'achat"""
    DRAFT = "draft"                    # Brouillon
    REQUESTED = "requested"            # Demandé
    APPROVED = "approved"              # Approuvé
    ORDERED = "ordered"                # Commandé fournisseur
    PARTIALLY_RECEIVED = "partially_received"  # Partiellement reçu
    RECEIVED = "received"              # Complètement reçu
    INVOICED = "invoiced"              # Facturé
    CANCELLED = "cancelled"            # Annulé

class PurchaseUrgency(Enum):
    """Niveaux d'urgence des achats"""
    LOW = "low"                        # Faible
    NORMAL = "normal"                  # Normale
    HIGH = "high"                      # Haute
    URGENT = "urgent"                  # Urgente

class Purchase(db.Model):
    """
    Bon d'achat fournisseur
    Gestion complète du processus d'achat avec workflow d'approbation
    """
    __tablename__ = 'purchases'
    
    # Identifiants
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    
    # Informations fournisseur
    supplier_name = db.Column(db.String(200), nullable=False)
    supplier_contact = db.Column(db.String(100))
    supplier_phone = db.Column(db.String(20))
    supplier_email = db.Column(db.String(120))
    supplier_address = db.Column(db.Text)
    
    # Statut et workflow
    status = db.Column(db.Enum(PurchaseStatus), default=PurchaseStatus.DRAFT, nullable=False)
    urgency = db.Column(db.Enum(PurchaseUrgency), default=PurchaseUrgency.NORMAL, nullable=False)
    
    # Utilisateurs et dates
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    requested_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approved_date = db.Column(db.DateTime, nullable=True)
    expected_delivery_date = db.Column(db.DateTime, nullable=True)
    received_date = db.Column(db.DateTime, nullable=True)
    
    # Montants et facturation
    subtotal_amount = db.Column(db.Numeric(12, 2), default=0.0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0.0)
    shipping_cost = db.Column(db.Numeric(12, 2), default=0.0)
    total_amount = db.Column(db.Numeric(12, 2), default=0.0)
    
    # Informations complémentaires
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)  # Notes internes non visibles fournisseur
    terms_conditions = db.Column(db.Text)
    payment_terms = db.Column(db.String(100))  # Ex: "30 jours net"
    
    # Stock destination par défaut
    default_stock_location = db.Column(db.String(50), default='ingredients_magasin')
    
    # Traçabilité
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='purchases_requested')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='purchases_approved')
    received_by = db.relationship('User', foreign_keys=[received_by_id], backref='purchases_received')
    
    items = db.relationship('PurchaseItem', backref='purchase', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Purchase, self).__init__(**kwargs)
        if not self.reference:
            self.generate_reference()
    
    def generate_reference(self):
        """Génère une référence unique pour le bon d'achat"""
        date_str = datetime.now().strftime('%Y%m%d')
        count = Purchase.query.filter(
            Purchase.reference.like(f'BA-{date_str}-%')
        ).count()
        self.reference = f'BA-{date_str}-{count + 1:04d}'
    
    @property
    def can_be_approved(self):
        """Peut être approuvé"""
        return self.status in [PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED]
    
    @property
    def can_be_ordered(self):
        """Peut être commandé"""
        return self.status == PurchaseStatus.APPROVED
    
    @property
    def can_receive_items(self):
        """Peut recevoir des marchandises"""
        return self.status in [PurchaseStatus.ORDERED, PurchaseStatus.PARTIALLY_RECEIVED]
    
    @property
    def is_completed(self):
        """Achat complètement terminé"""
        return self.status in [PurchaseStatus.RECEIVED, PurchaseStatus.INVOICED]
    
    @property
    def total_items_count(self):
        """Nombre total d'articles"""
        return self.items.count()
    
    @property
    def total_quantity_ordered(self):
        """Quantité totale commandée"""
        return sum(item.quantity_ordered for item in self.items)
    
    @property
    def total_quantity_received(self):
        """Quantité totale reçue"""
        return sum(item.quantity_received for item in self.items)
    
    @property
    def completion_percentage(self):
        """Pourcentage de réception"""
        if self.total_quantity_ordered == 0:
            return 0
        return (self.total_quantity_received / self.total_quantity_ordered) * 100
    
    @property
    def status_display(self):
        """Nom d'affichage du statut"""
        status_names = {
            PurchaseStatus.DRAFT: "Brouillon",
            PurchaseStatus.REQUESTED: "Demandé",
            PurchaseStatus.APPROVED: "Approuvé",
            PurchaseStatus.ORDERED: "Commandé",
            PurchaseStatus.PARTIALLY_RECEIVED: "Partiellement reçu",
            PurchaseStatus.RECEIVED: "Reçu",
            PurchaseStatus.INVOICED: "Facturé",
            PurchaseStatus.CANCELLED: "Annulé"
        }
        return status_names.get(self.status, self.status.value)
    
    @property
    def urgency_display(self):
        """Nom d'affichage de l'urgence"""
        urgency_names = {
            PurchaseUrgency.LOW: "Faible",
            PurchaseUrgency.NORMAL: "Normale", 
            PurchaseUrgency.HIGH: "Haute",
            PurchaseUrgency.URGENT: "Urgente"
        }
        return urgency_names.get(self.urgency, self.urgency.value)
    
    @property
    def status_color_class(self):
        """Classe CSS selon le statut"""
        status_colors = {
            PurchaseStatus.DRAFT: "secondary",
            PurchaseStatus.REQUESTED: "warning",
            PurchaseStatus.APPROVED: "info",
            PurchaseStatus.ORDERED: "primary",
            PurchaseStatus.PARTIALLY_RECEIVED: "warning",
            PurchaseStatus.RECEIVED: "success",
            PurchaseStatus.INVOICED: "success",
            PurchaseStatus.CANCELLED: "danger"
        }
        return status_colors.get(self.status, "secondary")
    
    @property
    def urgency_color_class(self):
        """Classe CSS selon l'urgence"""
        urgency_colors = {
            PurchaseUrgency.LOW: "success",
            PurchaseUrgency.NORMAL: "info",
            PurchaseUrgency.HIGH: "warning", 
            PurchaseUrgency.URGENT: "danger"
        }
        return urgency_colors.get(self.urgency, "info")
    
    def calculate_totals(self):
        """Calcule les totaux à partir des lignes"""
        self.subtotal_amount = sum(item.line_total for item in self.items)
        self.total_amount = self.subtotal_amount + (self.tax_amount or 0) + (self.shipping_cost or 0)
        return self.total_amount
    
    def approve(self, user_id):
        """Approuve le bon d'achat"""
        if self.can_be_approved:
            self.status = PurchaseStatus.APPROVED
            self.approved_by_id = user_id
            self.approved_date = datetime.utcnow()
            return True
        return False
    
    def mark_as_ordered(self):
        """Marque comme commandé chez le fournisseur"""
        if self.can_be_ordered:
            self.status = PurchaseStatus.ORDERED
            return True
        return False
    
    def check_completion_status(self):
        """Vérifie et met à jour le statut selon les réceptions"""
        if self.status not in [PurchaseStatus.ORDERED, PurchaseStatus.PARTIALLY_RECEIVED]:
            return
        
        total_ordered = self.total_quantity_ordered
        total_received = self.total_quantity_received
        
        if total_received == 0:
            # Aucune réception
            self.status = PurchaseStatus.ORDERED
        elif total_received >= total_ordered:
            # Réception complète
            self.status = PurchaseStatus.RECEIVED
            if not self.received_date:
                self.received_date = datetime.utcnow()
        else:
            # Réception partielle
            self.status = PurchaseStatus.PARTIALLY_RECEIVED
    
    def cancel(self):
        """Annule le bon d'achat"""
        if self.status not in [PurchaseStatus.RECEIVED, PurchaseStatus.INVOICED]:
            self.status = PurchaseStatus.CANCELLED
            return True
        return False
    
    def get_formatted_expected_delivery(self):
        """Date de livraison formatée"""
        if self.expected_delivery_date:
            return self.expected_delivery_date.strftime('%d/%m/%Y')
        return "Non définie"
    
    def is_overdue(self):
        """Vérifie si la livraison est en retard"""
        if not self.expected_delivery_date:
            return False
        return (self.expected_delivery_date < datetime.utcnow() and 
                self.status not in [PurchaseStatus.RECEIVED, PurchaseStatus.INVOICED, PurchaseStatus.CANCELLED])
    
    def __repr__(self):
        return f'<Purchase {self.reference}: {self.supplier_name}>'

class PurchaseItem(db.Model):
    """
    Ligne d'article dans un bon d'achat
    Gestion des quantités commandées vs reçues
    """
    __tablename__ = 'purchase_items'
    
    # Identifiants
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Quantités et prix
    quantity_ordered = db.Column(db.Numeric(10, 3), nullable=False)
    quantity_received = db.Column(db.Numeric(10, 3), default=0.0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0.0)  # Remise en %
    
    # Stock destination pour cet article
    stock_location = db.Column(db.String(50), default='ingredients_magasin')
    
    # Informations complémentaires
    description_override = db.Column(db.String(255))  # Description spécifique fournisseur
    supplier_reference = db.Column(db.String(100))     # Référence fournisseur
    notes = db.Column(db.Text)
    
    # Traçabilité réception
    received_date = db.Column(db.DateTime, nullable=True)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    product = db.relationship('Product', backref='purchase_items')
    received_by = db.relationship('User', foreign_keys=[received_by_id], backref='items_received')
    
    @property
    def line_subtotal(self):
        """Sous-total avant remise"""
        return Decimal(self.quantity_ordered) * Decimal(self.unit_price)
    
    @property
    def discount_amount(self):
        """Montant de la remise"""
        if self.discount_percentage:
            return self.line_subtotal * (Decimal(self.discount_percentage) / 100)
        return Decimal('0.00')
    
    @property
    def line_total(self):
        """Total de la ligne après remise"""
        return self.line_subtotal - self.discount_amount
    
    @property
    def effective_unit_price(self):
        """Prix unitaire effectif après remise"""
        if self.quantity_ordered == 0:
            return Decimal('0.00')
        return self.line_total / Decimal(self.quantity_ordered)
    
    @property
    def remaining_quantity(self):
        """Quantité restant à recevoir"""
        return max(0, Decimal(self.quantity_ordered) - Decimal(self.quantity_received))
    
    @property
    def is_fully_received(self):
        """Article complètement reçu"""
        return self.quantity_received >= self.quantity_ordered
    
    @property
    def reception_percentage(self):
        """Pourcentage de réception de cet article"""
        if self.quantity_ordered == 0:
            return 0
        return (self.quantity_received / self.quantity_ordered) * 100
    
    @property
    def display_name(self):
        """Nom d'affichage (override ou nom produit)"""
        return self.description_override or (self.product.name if self.product else "Produit supprimé")
    
    @property
    def stock_location_display(self):
        """Nom d'affichage de la localisation stock"""
        locations = {
            'comptoir': 'Stock Comptoir',
            'ingredients_local': 'Stock Local Production',
            'ingredients_magasin': 'Stock Magasin',
            'consommables': 'Stock Consommables'
        }
        return locations.get(self.stock_location, self.stock_location)
    
    def receive_quantity(self, quantity_received, user_id, stock_location=None):
        """
        Réceptionne une quantité de cet article
        Met à jour le stock selon la localisation définie
        """
        if quantity_received <= 0:
            return False, "La quantité doit être positive"
        
        if self.quantity_received + quantity_received > self.quantity_ordered:
            return False, f"Impossible de recevoir plus que commandé (Max: {self.remaining_quantity})"
        
        # Mise à jour des quantités
        self.quantity_received += quantity_received
        self.received_by_id = user_id
        self.received_date = datetime.utcnow()
        
        # Utilisation de la localisation spécifiée ou par défaut
        target_location = stock_location or self.stock_location
        
        # Mise à jour du stock produit
        if self.product:
            self.product.update_stock_location(target_location, float(quantity_received))
            
            # Création du mouvement de traçabilité
            from app.stock.models import update_stock_quantity, StockLocationType
            location_enum = getattr(StockLocationType, target_location.upper(), None)
            if location_enum:
                update_stock_quantity(
                    self.product.id,
                    location_enum,
                    float(quantity_received),
                    user_id,
                    reason=f"Réception achat {self.purchase.reference}",
                    order_id=None
                )
        
        return True, f"Réception de {quantity_received} unités effectuée"
    
    def get_formatted_quantity_ordered(self):
        """Quantité commandée formatée"""
        if self.quantity_ordered == int(self.quantity_ordered):
            return str(int(self.quantity_ordered))
        return f"{self.quantity_ordered:.2f}"
    
    def get_formatted_quantity_received(self):
        """Quantité reçue formatée"""
        if self.quantity_received == int(self.quantity_received):
            return str(int(self.quantity_received))
        return f"{self.quantity_received:.2f}"
    
    def get_formatted_line_total(self):
        """Total de ligne formaté"""
        return f"{self.line_total:.2f} DA"
    
    def __repr__(self):
        return f'<PurchaseItem {self.display_name}: {self.quantity_ordered}x{self.unit_price}>'

# Fonctions utilitaires pour les achats

def get_pending_purchases_count():
    """Retourne le nombre d'achats en attente d'approbation"""
    return Purchase.query.filter(
        Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
    ).count()

def get_overdue_purchases():
    """Retourne les achats en retard de livraison"""
    return Purchase.query.filter(
        and_(
            Purchase.expected_delivery_date < datetime.utcnow(),
            Purchase.status.in_([PurchaseStatus.ORDERED, PurchaseStatus.PARTIALLY_RECEIVED])
        )
    ).all()

def get_purchases_by_supplier(supplier_name):
    """Retourne les achats d'un fournisseur"""
    return Purchase.query.filter(
        Purchase.supplier_name.ilike(f'%{supplier_name}%')
    ).order_by(Purchase.requested_date.desc()).all()

def get_monthly_purchase_stats(year, month):
    """Statistiques d'achats pour un mois donné"""
    from sqlalchemy import extract, func
    
    purchases = Purchase.query.filter(
        and_(
            extract('year', Purchase.requested_date) == year,
            extract('month', Purchase.requested_date) == month,
            Purchase.status != PurchaseStatus.CANCELLED
        )
    ).all()
    
    return {
        'total_purchases': len(purchases),
        'total_amount': sum(p.total_amount for p in purchases),
        'completed_purchases': len([p for p in purchases if p.is_completed]),
        'pending_purchases': len([p for p in purchases if not p.is_completed])
    }
