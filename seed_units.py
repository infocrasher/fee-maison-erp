# Script d'insertion des unités (à exécuter une fois)
# Vous pouvez l'ajouter dans un fichier seed_units.py

from app import create_app
from extensions import db
from models import Unit

app = create_app()
with app.app_context():
    # Supprimer anciennes données si elles existent
    Unit.query.delete()
    
    # Unités de poids (base: grammes)
    weight_units = [
        ('250g', 'g', 250, 'weight', 1),
        ('500g', 'g', 500, 'weight', 2),
        ('1.8kg', 'g', 1800, 'weight', 3),
        ('2kg', 'g', 2000, 'weight', 4),
        ('3.8kg', 'g', 3800, 'weight', 5),
        ('5kg', 'g', 5000, 'weight', 6),
        ('10kg', 'g', 10000, 'weight', 7),
        ('25kg', 'g', 25000, 'weight', 8),
    ]
    
    # Unités de volume (base: millilitres)
    volume_units = [
        ('2L', 'ml', 2000, 'volume', 9),
        ('5L', 'ml', 5000, 'volume', 10),
    ]
    
    all_units = weight_units + volume_units
    
    for name, base_unit, factor, unit_type, order in all_units:
        unit = Unit(
            name=name,
            base_unit=base_unit,
            conversion_factor=factor,
            unit_type=unit_type,
            display_order=order
        )
        db.session.add(unit)
    
    db.session.commit()
    print(f"✅ {len(all_units)} unités créées avec succès")
