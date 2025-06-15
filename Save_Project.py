# -*- coding: utf-8 -*-
import os
import subprocess
import datetime
import shutil
import csv
from sqlalchemy import text
from app import create_app, db

# Répertoire de sauvegarde
HOME = os.path.expanduser("~")
BACKUP_DIR = os.path.join(HOME, "Documents", "Sauvgarde_FM_Gestion")

def ensure_backup_dir():
    """Crée le répertoire de sauvegarde s'il n'existe pas"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"📁 Répertoire de sauvegarde créé : {BACKUP_DIR}")
    return BACKUP_DIR

def get_all_table_names():
    """Récupère automatiquement tous les noms de tables de la DB"""
    app = create_app()
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables détectées : {tables}")
            return tables
        except Exception as e:
            print(f"⚠️ Erreur lors de la détection des tables : {e}")
            # Fallback sur la liste manuelle des tables vues dans le dump
            return ["alembic_version", "categories", "users", "orders", "products", 
                    "order_items", "recipes", "recipe_ingredients"]

def backup_postgres_db():
    """Sauvegarde physique de la base PostgreSQL via pg_dump"""
    app = create_app()
    with app.app_context():
        db_uri = db.engine.url
        
        if not db_uri.drivername.startswith("postgresql"):
            print("❌ La base n'est pas PostgreSQL.")
            return None
        
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(BACKUP_DIR, f"FM_Gestion_DB_{date_str}.backup")
        
        # Construction de la commande pg_dump
        pg_dump_cmd = [
            "pg_dump",
            "-h", str(db_uri.host or "localhost"),
            "-U", str(db_uri.username),
            "-p", str(db_uri.port or 5432),
            "-F", "c",   # format custom (compressé)
            "-b",        # include blobs
            "-v",        # verbose
            "-f", dest,  # output file
            str(db_uri.database)
        ]
        
        print(f"👉 Exécution : {' '.join(pg_dump_cmd)}")
        
        # Configuration de l'environnement avec mot de passe
        env = os.environ.copy()
        if db_uri.password:
            env["PGPASSWORD"] = str(db_uri.password)
        
        try:
            subprocess.check_call(pg_dump_cmd, env=env)
            print(f"✅ Dump PostgreSQL effectué : {dest}")
            
            # Vérifier la taille du fichier
            size_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f"📊 Taille de la sauvegarde : {size_mb:.2f} MB")
            
            return dest
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors du dump PostgreSQL :\n{e}")
        except FileNotFoundError:
            print("❌ pg_dump non trouvé. Assurez-vous que PostgreSQL est installé.")
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")
    
    return None

def export_table_to_csv(table_name):
    """Sauvegarde d'une table sous forme CSV - VERSION CORRIGÉE"""
    app = create_app()
    with app.app_context():
        try:
            # Vérification que la table existe
            inspector = db.inspect(db.engine)
            if table_name not in inspector.get_table_names():
                print(f"❌ Table '{table_name}' introuvable dans la base.")
                return False
            
            # Export via requête SQL - NOUVELLE SYNTAXE SQLAlchemy
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = os.path.join(BACKUP_DIR, f"{table_name}_{date_str}.csv")
            
            # CORRECTION : Utiliser db.session au lieu de db.engine.execute
            query = text(f"SELECT * FROM {table_name}")
            result = db.session.execute(query)
            
            # Écriture du CSV
            with open(csv_file, "w", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                
                # En-têtes
                writer.writerow(result.keys())
                
                # Données
                row_count = 0
                for row in result:
                    # Conversion des valeurs pour éviter les erreurs d'encodage
                    clean_row = []
                    for value in row:
                        if value is None:
                            clean_row.append("")
                        elif isinstance(value, (datetime.datetime, datetime.date)):
                            clean_row.append(str(value))
                        else:
                            clean_row.append(str(value))
                    writer.writerow(clean_row)
                    row_count += 1
            
            print(f"✅ Table '{table_name}' sauvegardée : {row_count} lignes → {csv_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de '{table_name}': {e}")
            return False

def backup_application_files():
    """Sauvegarde des fichiers de l'application (code source)"""
    try:
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        app_backup = os.path.join(BACKUP_DIR, f"FM_Gestion_APP_{date_str}")
        
        # Répertoire source (répertoire courant)
        source_dir = "."
        
        # Copie en excluant certains dossiers
        def ignore_patterns(dir, files):
            return [f for f in files if f in ['venv', '__pycache__', '.git', 'node_modules', '*.pyc']]
        
        shutil.copytree(source_dir, app_backup, ignore=ignore_patterns)
        
        # Compression du dossier
        shutil.make_archive(app_backup, 'zip', app_backup)
        shutil.rmtree(app_backup)  # Supprimer le dossier non compressé
        
        print(f"✅ Code source sauvegardé : {app_backup}.zip")
        return f"{app_backup}.zip"
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde du code : {e}")
        return None

def show_backup_statistics():
    """Affiche les statistiques des sauvegardes existantes"""
    try:
        files = [f for f in os.listdir(BACKUP_DIR) if os.path.isfile(os.path.join(BACKUP_DIR, f))]
        if not files:
            print("📊 Aucune sauvegarde existante")
            return
        
        total_size = 0
        backup_count = 0
        oldest_date = None
        newest_date = None
        
        for filename in files:
            file_path = os.path.join(BACKUP_DIR, filename)
            file_size = os.path.getsize(file_path)
            total_size += file_size
            
            file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
            if oldest_date is None or file_time < oldest_date:
                oldest_date = file_time
            if newest_date is None or file_time > newest_date:
                newest_date = file_time
            
            backup_count += 1
        
        total_size_mb = total_size / (1024 * 1024)
        
        print(f"📊 === STATISTIQUES SAUVEGARDES ===")
        print(f"📁 Nombre de fichiers : {backup_count}")
        print(f"💾 Taille totale : {total_size_mb:.2f} MB")
        if oldest_date:
            print(f"📅 Plus ancienne : {oldest_date.strftime('%d/%m/%Y %H:%M')}")
        if newest_date:
            print(f"📅 Plus récente : {newest_date.strftime('%d/%m/%Y %H:%M')}")
            
    except Exception as e:
        print(f"⚠️ Erreur lors du calcul des statistiques : {e}")

def main():
    """Fonction principale de sauvegarde"""
    print("🚀 === SAUVEGARDE ERP FÉE MAISON ===")
    print(f"📅 Date : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Créer le répertoire de sauvegarde
    ensure_backup_dir()
    
    # Afficher les statistiques des sauvegardes existantes
    show_backup_statistics()
    
    success_count = 0
    total_operations = 0
    
    # 1. Sauvegarde de la base de données complète
    print("\n🗄️ === SAUVEGARDE BASE DE DONNÉES ===")
    total_operations += 1
    if backup_postgres_db():
        success_count += 1
    
    # 2. Sauvegarde des tables en CSV - AVEC CONTEXTE CORRIGÉ
    print("\n📊 === SAUVEGARDE TABLES CSV ===")
    tables = get_all_table_names()
    for table_name in tables:
        total_operations += 1
        if export_table_to_csv(table_name):
            success_count += 1
    
    # 3. Sauvegarde du code source
    print("\n💾 === SAUVEGARDE CODE SOURCE ===")
    total_operations += 1
    if backup_application_files():
        success_count += 1
    
    # Résumé final
    print(f"\n🎉 === SAUVEGARDE TERMINÉE ===")
    print(f"✅ Succès : {success_count}/{total_operations} opérations")
    print(f"📁 Répertoire : {BACKUP_DIR}")
    
    # Afficher la taille totale finale
    try:
        total_size = sum(os.path.getsize(os.path.join(BACKUP_DIR, f)) 
                        for f in os.listdir(BACKUP_DIR) 
                        if os.path.isfile(os.path.join(BACKUP_DIR, f)))
        total_size_mb = total_size / (1024 * 1024)
        print(f"📊 Taille totale du dossier : {total_size_mb:.2f} MB")
    except:
        pass
    
    print("💾 Toutes les sauvegardes sont conservées.")

if __name__ == "__main__":
    main()
