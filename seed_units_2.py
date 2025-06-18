# Script de récupération des unités de base
from app import create_app
from extensions import db
from models import Unit

app = create_app()
with app.app_context():
    
    # Unités de base essentielles à recréer
    base_units = [
        ('g', 'g', 1, 'weight', 100),          # Gramme (unité de base poids)
        ('kg', 'g', 1000, 'weight', 101),      # Kilogramme  
        ('ml', 'ml', 1, 'volume', 102),        # Millilitre (unité de base volume)
        ('L', 'ml', 1000, 'volume', 103),      # Litre ← Votre "103" !
        ('Pièce', 'piece', 1, 'count', 104),   # Pièce/unité
        ('unité', 'piece', 1, 'count', 105),   # Unité
    ]
    
    for name, base_unit, factor, unit_type, order in base_units:
        # Vérifier si elle n'existe pas déjà
        existing = Unit.query.filter_by(name=name).first()
        if not existing:
            unit = Unit(
                name=name,
                base_unit=base_unit,
                conversion_factor=factor,
                unit_type=unit_type,
                display_order=order
            )
            db.session.add(unit)
            print(f"✅ Ajout unité: {name}")
    
    db.session.commit()
    print("🎯 Unités de base restaurées avec succès")
