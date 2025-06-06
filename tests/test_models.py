# tests/test_models.py
from models import User
# from extensions import db # db_session est utilisé via la fixture
# werkzeug.security n'est plus nécessaire ici car on utilise les méthodes du modèle

def test_new_user_creation_and_password_check(db_session): # Utilise la fixture db_session
    """Teste la création d'un nouvel utilisateur et la vérification du mot de passe via les méthodes du modèle."""
    # La fixture db_session fournit une session DB propre et gère create_all/drop_all/rollback.
    # Elle s'exécute déjà dans un app_context.
    
    user = User(username='testmodeluser', email='testmodel@example.com', role='user')
    user.set_password('password123')

    db_session.add(user)
    db_session.commit()

    # Il est préférable de requêter à nouveau pour s'assurer de la persistance et de l'état
    retrieved_user = User.query.filter_by(username='testmodeluser').first()
    
    assert retrieved_user is not None
    assert retrieved_user.id is not None
    assert retrieved_user.username == 'testmodeluser'
    assert retrieved_user.email == 'testmodel@example.com'
    assert retrieved_user.password_hash is not None
    assert retrieved_user.role == 'user'

    assert retrieved_user.check_password('password123')
    assert not retrieved_user.check_password('wrongpassword')