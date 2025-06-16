"""
Modèles pour la gestion avancée des stocks
Module: app/stock/models.py
Auteur: ERP Fée Maison
"""

from datetime import datetime
from enum import Enum
from extensions import db

class StockMovementType(Enum):
    """Types de mouvements de stock possibles"""
    ENTREE = "entree"                    # Réception marchandise
    SORTIE = "sortie"                    # Consommation/vente
    TRANSFERT_SORTIE = "transfert_sortie"  # Transfert sortant
    TRANSFERT_ENTREE = "transfert_entree"  # Transfert entrant
    AJUSTEMENT_POSITIF = "ajustement_positif"  # Correction +
    AJUSTEMENT_NEGATIF = "ajustement_negatif"  # Correction -
    PRODUCTION = "production"            # Ordre de production
    VENTE = "vente"                     # Vente comptoir
    INVENTAIRE = "inventaire"           # Rectification inventaire

class StockLocationType(Enum):
    """4 Types de stocks définis pour Fée Maison"""
    COMPTOIR = "comptoir"                    # Produits finis vitrine
    INGREDIENTS_LOCAL = "ingredients_local"   # Production immédiate
    INGREDIENTS_MAGASIN = "ingredients_magasin"  # Stock de sécurité
    CONSOMMABLES = "consommables"            # Emballages, matériel

class TransferStatus(Enum):
    """Statuts des transferts entre stocks"""
    DRAFT = "draft"           # Brouillon
    REQUESTED = "requested"   # Demandé
    APPROVED = "approved"     # Approuvé
    IN_TRANSIT = "in_transit" # En cours
    COMPLETED = "completed"   # Terminé
    CANCELLED = "cancelled"   # Annulé

class StockMovement(db.Model):
    """
    Historique complet des mouvements de stock
    Traçabilité : Qui, Quoi, Quand, Pourquoi, Combien
    """
    __tablename__ = 'stock_movements'
    
    # Identifiants
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    
    # Produit et localisation
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stock_location = db.Column(db.Enum(StockLocationType), nullable=False)
    
    # Détails du mouvement
    movement_type = db.Column(db.Enum(StockMovementType), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Positif=entrée, Négatif=sortie
    unit_cost = db.Column(db.Float, default=0.0)
    total_value = db.Column(db.Float, default=0.0)
    
    # Stock avant/après (pour vérification)
    stock_before = db.Column(db.Float, default=0.0)
    stock_after = db.Column(db.Float, default=0.0)
    
    # Références et traçabilité
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('stock_transfers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Informations complémentaires
    reason = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    product = db.relationship('Product', backref='stock_movements')
    order = db.relationship('Order', backref='related_stock_movements')
    user = db.relationship('User', backref='stock_movements_created')
    
    def __init__(self, **kwargs):
        super(StockMovement, self).__init__(**kwargs)
        if not self.reference:
            self.generate_reference()
        if self.quantity and self.unit_cost:
            self.total_value = abs(self.quantity) * self.unit_cost
    
    def generate_reference(self):
        """Génère une référence unique pour le mouvement"""
        date_str = datetime.now().strftime('%Y%m%d')
        count = StockMovement.query.filter(
            StockMovement.reference.like(f'MVT-{date_str}-%')
        ).count()
        self.reference = f'MVT-{date_str}-{count + 1:04d}'
    
    @property
    def is_positive(self):
        """Mouvement positif (entrée)"""
        return self.quantity > 0
    
    @property
    def is_negative(self):
        """Mouvement négatif (sortie)"""
        return self.quantity < 0
    
    @property
    def movement_value(self):
        """Valeur absolue du mouvement"""
        return abs(self.quantity) * (self.unit_cost or 0)
    
    def __repr__(self):
        return f'<StockMovement {self.reference}: {self.product.name if self.product else "N/A"} {self.quantity:+.2f}>'

class StockTransfer(db.Model):
    """
    Transferts entre les 4 types de stocks
    Workflow: Draft → Requested → Approved → In Transit → Completed
    """
    __tablename__ = 'stock_transfers'
    
    # Identifiants
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    
    # Localisations source et destination
    source_location = db.Column(db.Enum(StockLocationType), nullable=False)
    destination_location = db.Column(db.Enum(StockLocationType), nullable=False)
    
    # Statut et workflow
    status = db.Column(db.Enum(TransferStatus), default=TransferStatus.DRAFT, nullable=False)
    
    # Utilisateurs et dates
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    requested_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approved_date = db.Column(db.DateTime, nullable=True)
    scheduled_date = db.Column(db.DateTime, nullable=True)
    completed_date = db.Column(db.DateTime, nullable=True)
    
    # Informations complémentaires
    reason = db.Column(db.String(255))
    notes = db.Column(db.Text)
    priority = db.Column(db.String(20), default='normal')  # urgent, high, normal, low
    
    # Relations
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='transfers_requested')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='transfers_approved')
    completed_by = db.relationship('User', foreign_keys=[completed_by_id], backref='transfers_completed')
    
    # Relation avec les mouvements de stock
    movements = db.relationship('StockMovement', backref='stock_transfer', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(StockTransfer, self).__init__(**kwargs)
        if not self.reference:
            self.generate_reference()
    
    def generate_reference(self):
        """Génère une référence unique pour le transfert"""
        date_str = datetime.now().strftime('%Y%m%d')
        # Préfixe selon type de transfert
        prefix_map = {
            'magasin_to_local': 'TML',      # Transfer Magasin to Local
            'local_to_magasin': 'TLM',      # Transfer Local to Magasin
            'production_to_comptoir': 'TPC', # Transfer Production to Comptoir
            'comptoir_to_local': 'TCL',     # Transfer Comptoir to Local
        }
        
        transfer_type = f"{self.source_location.value}_to_{self.destination_location.value}"
        prefix = prefix_map.get(transfer_type, 'TRF')
        
        count = StockTransfer.query.filter(
            StockTransfer.reference.like(f'{prefix}-{date_str}-%')
        ).count()
        self.reference = f'{prefix}-{date_str}-{count + 1:03d}'
    
    @property
    def is_pending(self):
        """Transfert en attente d'approbation"""
        return self.status in [TransferStatus.DRAFT, TransferStatus.REQUESTED]
    
    @property
    def is_active(self):
        """Transfert en cours"""
        return self.status in [TransferStatus.APPROVED, TransferStatus.IN_TRANSIT]
    
    @property
    def is_completed(self):
        """Transfert terminé"""
        return self.status == TransferStatus.COMPLETED
    
    @property
    def can_be_approved(self):
        """Peut être approuvé"""
        return self.status == TransferStatus.REQUESTED
    
    @property
    def can_be_completed(self):
        """Peut être marqué comme terminé"""
        return self.status in [TransferStatus.APPROVED, TransferStatus.IN_TRANSIT]
    
    @property
    def source_location_display(self):
        """Nom affiché de la localisation source"""
        names = {
            StockLocationType.COMPTOIR: "Stock Comptoir",
            StockLocationType.INGREDIENTS_LOCAL: "Stock Local Production",
            StockLocationType.INGREDIENTS_MAGASIN: "Stock Magasin",
            StockLocationType.CONSOMMABLES: "Stock Consommables"
        }
        return names.get(self.source_location, self.source_location.value)
    
    @property
    def destination_location_display(self):
        """Nom affiché de la localisation destination"""
        names = {
            StockLocationType.COMPTOIR: "Stock Comptoir",
            StockLocationType.INGREDIENTS_LOCAL: "Stock Local Production",
            StockLocationType.INGREDIENTS_MAGASIN: "Stock Magasin",
            StockLocationType.CONSOMMABLES: "Stock Consommables"
        }
        return names.get(self.destination_location, self.destination_location.value)
    
    @property
    def total_items(self):
        """Nombre total d'articles dans le transfert"""
        return len(self.transfer_lines)
    
    @property
    def total_value(self):
        """Valeur totale du transfert"""
        return sum(line.line_value for line in self.transfer_lines)
    
    def approve(self, user_id):
        """Approuve le transfert"""
        if self.can_be_approved:
            self.status = TransferStatus.APPROVED
            self.approved_by_id = user_id
            self.approved_date = datetime.utcnow()
            return True
        return False
    
    def start_transit(self):
        """Démarre le transit"""
        if self.status == TransferStatus.APPROVED:
            self.status = TransferStatus.IN_TRANSIT
            return True
        return False
    
    def complete(self, user_id):
        """Termine le transfert"""
        if self.can_be_completed:
            self.status = TransferStatus.COMPLETED
            self.completed_by_id = user_id
            self.completed_date = datetime.utcnow()
            return True
        return False
    
    def cancel(self):
        """Annule le transfert"""
        if self.status not in [TransferStatus.COMPLETED, TransferStatus.CANCELLED]:
            self.status = TransferStatus.CANCELLED
            return True
        return False
    
    def __repr__(self):
        return f'<StockTransfer {self.reference}: {self.source_location.value} → {self.destination_location.value}>'

class StockTransferLine(db.Model):
    """
    Lignes de détail des transferts
    Chaque ligne = un produit avec quantité demandée/transférée
    """
    __tablename__ = 'stock_transfer_lines'
    
    # Identifiants
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('stock_transfers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Quantités
    quantity_requested = db.Column(db.Float, nullable=False)
    quantity_approved = db.Column(db.Float, default=0.0)
    quantity_transferred = db.Column(db.Float, default=0.0)
    
    # Coûts et valeurs
    unit_cost = db.Column(db.Float, default=0.0)
    
    # Informations complémentaires
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    transfer = db.relationship('StockTransfer', backref='transfer_lines')
    product = db.relationship('Product', backref='transfer_lines')
    
    @property
    def line_value(self):
        """Valeur de la ligne"""
        return self.quantity_requested * (self.unit_cost or 0)
    
    @property
    def is_fully_transferred(self):
        """Ligne complètement transférée"""
        return self.quantity_transferred >= self.quantity_requested
    
    @property
    def remaining_quantity(self):
        """Quantité restant à transférer"""
        return max(0, self.quantity_requested - self.quantity_transferred)
    
    @property
    def transfer_percentage(self):
        """Pourcentage de transfert effectué"""
        if self.quantity_requested == 0:
            return 0
        return (self.quantity_transferred / self.quantity_requested) * 100
    
    def __repr__(self):
        return f'<TransferLine {self.product.name if self.product else "N/A"}: {self.quantity_requested:.2f}>'

# Fonctions utilitaires pour les stocks

def get_stock_by_location(product_id, location_type):
    """
    Récupère le stock actuel d'un produit dans une localisation
    
    Args:
        product_id (int): ID du produit
        location_type (StockLocationType): Type de localisation
    
    Returns:
        float: Quantité en stock
    """
    from models import Product
    
    # Mapping vers les attributs du modèle Product
    location_attrs = {
        StockLocationType.COMPTOIR: 'stock_comptoir',
        StockLocationType.INGREDIENTS_LOCAL: 'stock_ingredients_local', 
        StockLocationType.INGREDIENTS_MAGASIN: 'stock_ingredients_magasin',
        StockLocationType.CONSOMMABLES: 'stock_consommables'
    }
    
    attr_name = location_attrs.get(location_type)
    if not attr_name:
        return 0.0
    
    product = Product.query.get(product_id)
    if not product:
        return 0.0
    
    return getattr(product, attr_name, 0.0)

def update_stock_quantity(product_id, location_type, quantity_change, user_id, reason=None, order_id=None):
    """
    Met à jour le stock et crée un mouvement de traçabilité
    
    Args:
        product_id (int): ID du produit
        location_type (StockLocationType): Localisation du stock
        quantity_change (float): Changement de quantité (+ ou -)
        user_id (int): ID de l'utilisateur effectuant l'opération
        reason (str): Raison du mouvement
        order_id (int): ID de la commande liée (optionnel)
    
    Returns:
        bool: Succès de l'opération
    """
    from models import Product
    
    try:
        # Récupération du produit
        product = Product.query.get(product_id)
        if not product:
            return False
        
        # Mapping vers les attributs du modèle Product
        location_attrs = {
            StockLocationType.COMPTOIR: 'stock_comptoir',
            StockLocationType.INGREDIENTS_LOCAL: 'stock_ingredients_local',
            StockLocationType.INGREDIENTS_MAGASIN: 'stock_ingredients_magasin',
            StockLocationType.CONSOMMABLES: 'stock_consommables'
        }
        
        attr_name = location_attrs.get(location_type)
        if not attr_name:
            return False
        
        # Stock avant modification
        stock_before = getattr(product, attr_name, 0.0)
        
        # Nouveau stock après modification
        stock_after = max(0, stock_before + quantity_change)
        
        # Mise à jour du stock
        setattr(product, attr_name, stock_after)
        
        # Détermination du type de mouvement
        if quantity_change > 0:
            movement_type = StockMovementType.ENTREE
        else:
            movement_type = StockMovementType.SORTIE
        
        # Création du mouvement de traçabilité
        movement = StockMovement(
            product_id=product_id,
            stock_location=location_type,
            movement_type=movement_type,
            quantity=quantity_change,
            unit_cost=product.cost_price or 0.0,
            stock_before=stock_before,
            stock_after=stock_after,
            user_id=user_id,
            order_id=order_id,
            reason=reason
        )
        
        # Sauvegarde
        db.session.add(movement)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur mise à jour stock: {e}")
        return False
