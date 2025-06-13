from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """
    Décorateur qui vérifie si l'utilisateur actuel est un administrateur.
    Doit être utilisé APRÈS @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # current_user.is_authenticated est déjà vérifié par @login_required
        # mais une double vérification ne fait pas de mal, ou on peut la retirer si @login_required est toujours avant.
        if not current_user.is_authenticated or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            abort(403)  # Accès interdit
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Décorateur générique pour vérifier un rôle spécifique.
    Usage: @role_required('admin') ou @role_required('manager')
    Doit être utilisé APRÈS @login_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # ✅ CORRECTION : Utilise current_user.role directement au lieu de has_role()
            if not current_user.is_authenticated or not hasattr(current_user, 'role') or current_user.role != role_name:
                abort(403) # Accès interdit
            return f(*args, **kwargs)
        return decorated_function
    return decorator
