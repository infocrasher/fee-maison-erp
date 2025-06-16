import os
from flask import Flask, g, request
from datetime import datetime
from extensions import db, migrate, login_manager, csrf
from config import Config
from config import DevelopmentConfigPostgreSQL

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfigPostgreSQL) 

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Request tracking
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = datetime.utcnow() - g.start_time
            total_ms = duration.total_seconds() * 1000
            if total_ms > 1000:  # Only log slow requests
                print(f"⏱️ Slow request: {request.endpoint} took {total_ms:.0f}ms")
        return response

    # Template context processors
    @app.context_processor
    def inject_global_vars():
        try:
            from models import Order
            from app.employees.models import Employee
            
            # Safe query execution with error handling
            try:
                pending_orders_count = Order.query.filter_by(status='pending').count()
            except Exception as e:
                print(f"Error counting pending orders: {e}")
                pending_orders_count = 0
            
            try:
                total_employees = Employee.query.count()
            except Exception as e:
                print(f"Error counting employees: {e}")
                total_employees = 0
            
            return {
                'pending_orders_count': pending_orders_count,
                'total_employees': total_employees,
                'current_year': datetime.now().year
            }
        except ImportError as e:
            print(f"Import error in context processor: {e}")
            return {
                'pending_orders_count': 0,
                'total_employees': 0,
                'current_year': datetime.now().year
            }

    # Custom template filters
    @app.template_filter('currency')
    def currency_filter(amount):
        """Format currency with DA symbol"""
        if amount is None:
            return "0,00 DA"
        try:
            return f"{amount:,.2f} DA".replace(',', ' ')
        except (ValueError, TypeError):
            return "0,00 DA"

    @app.template_filter('datetime_format')
    def datetime_format_filter(dt, format='%d/%m/%Y %H:%M'):
        """Format datetime for display"""
        if dt is None:
            return ""
        try:
            return dt.strftime(format)
        except (ValueError, AttributeError):
            return str(dt)

    # Register blueprints
    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # from app.categories import bp as categories_bp
    # app.register_blueprint(categories_bp)

    from app.products.routes import products as products_blueprint
    app.register_blueprint(products_blueprint, url_prefix='/products')

    from app.recipes.routes import recipes as recipes_blueprint
    app.register_blueprint(recipes_blueprint, url_prefix='/recipes')

    from app.orders.routes import orders as orders_blueprint
    app.register_blueprint(orders_blueprint, url_prefix='/orders')

    from app.orders.dashboard_routes import dashboard as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')

    from app.orders.status_routes import status as status_blueprint
    app.register_blueprint(status_blueprint, url_prefix='/status')

    from app.employees.routes import employees as employees_blueprint
    app.register_blueprint(employees_blueprint, url_prefix='/employees')

    # CORRECTION : Enregistrement des nouveaux blueprints avec import automatique
    # Les routes sont maintenant importées automatiquement dans les __init__.py des modules
    
    # Blueprint Stock - Nouveau système 4 localisations
    try:
        from app.stock import bp as stock_bp
        app.register_blueprint(stock_bp)
        print("✅ Blueprint stock enregistré avec succès")
    except ImportError as e:
        print(f"⚠️ Blueprint stock non disponible: {e}")
    except Exception as e:
        print(f"❌ Erreur blueprint stock: {e}")
    
    # Blueprint Purchases - Gestion achats fournisseurs
    try:
        from app.purchases import bp as purchases_bp
        app.register_blueprint(purchases_bp)
        print("✅ Blueprint purchases enregistré avec succès")
    except ImportError as e:
        print(f"⚠️ Blueprint purchases non disponible: {e}")
    except Exception as e:
        print(f"❌ Erreur blueprint purchases: {e}")

    # CLI commands
    @app.cli.command("create-admin")
    def create_admin():
        """Create an admin user"""
        from models import User
        
        username = input("Nom d'utilisateur admin: ")
        email = input("Email admin: ")
        password = input("Mot de passe admin: ")
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"❌ L'utilisateur '{username}' existe déjà")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"❌ L'email '{email}' est déjà utilisé")
            return
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            role='admin'
        )
        admin_user.set_password(password)
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Utilisateur admin '{username}' créé avec succès")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la création: {e}")

    @app.cli.command("stats")
    def show_stats():
        """Show application statistics"""
        try:
            from models import User, Product, Order, Category
            from app.employees.models import Employee
            
            print("\n📊 STATISTIQUES DE L'APPLICATION")
            print("=" * 50)
            
            # Users
            total_users = User.query.count()
            admin_users = User.query.filter_by(role='admin').count()
            print(f"👥 Utilisateurs: {total_users} (dont {admin_users} admins)")
            
            # Products and Categories
            total_products = Product.query.count()
            total_categories = Category.query.count()
            print(f"📦 Produits: {total_products} dans {total_categories} catégories")
            
            # Orders
            total_orders = Order.query.count()
            pending_orders = Order.query.filter_by(status='pending').count()
            completed_orders = Order.query.filter_by(status='completed').count()
            print(f"🛒 Commandes: {total_orders} (en attente: {pending_orders}, terminées: {completed_orders})")
            
            # Employees
            total_employees = Employee.query.count()
            print(f"👨‍💼 Employés: {total_employees}")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Erreur lors du calcul des statistiques: {e}")

    return app
