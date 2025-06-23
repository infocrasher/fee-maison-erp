"""
Module de gestion centralisée pour les emplacements de stock.

Ce module agit comme une couche d'abstraction pour faire la correspondance
entre la terminologie métier (ex: 'Labo A') et la structure de la base de données
(ex: la colonne 'stock_ingredients_magasin').
"""

class StockLocationManager:
    """
    Fournit des méthodes statiques pour gérer les emplacements de stock
    sans avoir besoin d'un modèle de base de données dédié pour l'instant.
    """
    
    # Dictionnaire de correspondance : Clé métier -> Nom de la colonne en BDD
    # C'est le cœur de notre "traducteur".
    STOCK_MAPPINGS = {
        'labo_a': 'stock_ingredients_magasin',
        'labo_b': 'stock_ingredients_local',
        # On peut ajouter les autres pour être complet
        'reserve': 'stock_ingredients_magasin', # Si "Labo A" est aussi la réserve principale
        'comptoir': 'stock_comptoir',
        'consommables': 'stock_consommables'
    }

    # Liste des emplacements de production valides pour les recettes
    PRODUCTION_LOCATIONS = [
        ('ingredients_magasin', 'Labo A (Réserve)'),
        ('ingredients_local', 'Labo B')
    ]

    @classmethod
    def get_column_name(cls, location_key: str) -> str | None:
        """
        Retourne le nom de la colonne de la base de données pour une clé métier donnée.
        
        :param location_key: La clé métier (ex: 'labo_a').
        :return: Le nom de la colonne (ex: 'stock_ingredients_magasin') ou None si non trouvé.
        """
        # On s'assure que la clé est en minuscule pour éviter les erreurs de casse
        return cls.STOCK_MAPPINGS.get(location_key.lower())

    @classmethod
    def get_production_choices(cls) -> list:
        """

        Retourne une liste de tuples (valeur, label) pour les formulaires WTForms,
        permettant de sélectionner un lieu de production.
        """
        return cls.PRODUCTION_LOCATIONS