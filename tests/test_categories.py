# tests/test_categories.py
import pytest
from flask import url_for
from models import User, Category, Product
from decimal import Decimal 

def test_list_categories_page_unauthorized_redirects(client, app):
    with app.test_request_context():
        response_no_redirect = client.get(url_for('list_categories'), follow_redirects=False)
        expected_login_url_path = url_for('login')
    assert response_no_redirect.status_code == 302
    assert expected_login_url_path in response_no_redirect.location
    with app.test_request_context():
        response_redirected = client.get(url_for('list_categories'), follow_redirects=True)
    assert "Connexion" in response_redirected.data.decode('utf-8')

def test_list_categories_page_as_admin(admin_client, app):
    with app.test_request_context():
        response = admin_client.get(url_for('list_categories'))
    assert response.status_code == 200
    assert "Gestion des Catégories" in response.data.decode('utf-8')

def test_new_category_page_as_admin(admin_client, app):
    with app.test_request_context():
        response = admin_client.get(url_for('new_category'))
    assert response.status_code == 200
    assert "Nouvelle Catégorie" in response.data.decode('utf-8')

def test_create_new_category_as_admin(admin_client, app, db_session):
    with app.app_context():
        initial_cat_count = db_session.query(Category).count()

    category_data = {
        'name': 'Fruits Frais Test Categories',
        'description': 'Fruits de saison frais et savoureux pour test categories'
    }
    with app.test_request_context():
        response = admin_client.post(url_for('new_category'), data=category_data, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Nouvelle catégorie ajoutée avec succès !" in response.data.decode('utf-8')
    
    with app.app_context():
        assert db_session.query(Category).count() == initial_cat_count + 1
        new_cat = db_session.query(Category).filter_by(name='Fruits Frais Test Categories').first()
        assert new_cat is not None
        assert new_cat.description == 'Fruits de saison frais et savoureux pour test categories'

def test_create_new_category_duplicate_name_as_admin(admin_client, app, db_session):
    existing_cat_name = 'Légumes Test Duplication'
    with app.app_context():
        cat1 = db_session.query(Category).filter_by(name=existing_cat_name).first()
        if not cat1:
            cat1 = Category(name=existing_cat_name, description='Légumes de saison pour test duplication')
            db_session.add(cat1)
            db_session.commit()
        initial_cat_count = db_session.query(Category).count()

    category_data_duplicate = { 'name': existing_cat_name, 'description': 'Autre description' }
    with app.test_request_context():
        response = admin_client.post(url_for('new_category'), data=category_data_duplicate, follow_redirects=False) 
    
    assert response.status_code == 200 
    # CORRECTION BASÉE SUR CategoryForm.validate_name: raise ValidationError('Une catégorie avec ce nom existe déjà.')
    assert "Une catégorie avec ce nom existe déjà." in response.data.decode('utf-8')
    
    with app.app_context():
        assert db_session.query(Category).count() == initial_cat_count

def test_edit_category_page_as_admin(admin_client, app, db_session):
    with app.app_context():
        test_category = Category(name='Catégorie à Modifier', description='Description originale')
        db_session.add(test_category)
        db_session.commit()
        category_id = test_category.id

    with app.test_request_context():
        response = admin_client.get(url_for('edit_category', category_id=category_id))
    assert response.status_code == 200
    assert "Modifier la Catégorie" in response.data.decode('utf-8')
    assert "Catégorie à Modifier" in response.data.decode('utf-8') 
    assert "Description originale" in response.data.decode('utf-8') 

def test_edit_category_submit_as_admin(admin_client, app, db_session):
    with app.app_context():
        test_category = Category(name='Catégorie Originale Edit', description='Description originale pour edit')
        db_session.add(test_category)
        db_session.commit()
        category_id = test_category.id

    updated_data = { 'name': 'Catégorie Modifiée Edit', 'description': 'Description mise à jour pour edit' }
    with app.test_request_context():
        response = admin_client.post(url_for('edit_category', category_id=category_id), 
                                   data=updated_data, follow_redirects=True)
    assert response.status_code == 200
    assert "Catégorie mise à jour avec succès !" in response.data.decode('utf-8') 
    
    with app.app_context():
        updated_category = db_session.get(Category, category_id)
        assert updated_category is not None
        assert updated_category.name == 'Catégorie Modifiée Edit'
        assert updated_category.description == 'Description mise à jour pour edit'

def test_edit_category_submit_invalid_data_as_admin(admin_client, app, db_session):
    with app.app_context():
        category1_edit_invalid = Category(name='Cat 1 Edit Invalid', description='Desc 1')
        category2_edit_invalid = Category(name='Cat 2 Edit Invalid', description='Desc 2')
        db_session.add_all([category1_edit_invalid, category2_edit_invalid])
        db_session.commit()
        category1_id = category1_edit_invalid.id

    invalid_data_empty = { 'name': '', 'description': 'Description valide' }
    with app.test_request_context():
        response_empty = admin_client.post(url_for('edit_category', category_id=category1_id), 
                                   data=invalid_data_empty, follow_redirects=False) 
    assert response_empty.status_code == 200 
    assert "Le nom de la catégorie est requis." in response_empty.data.decode('utf-8')

    invalid_data_duplicate = { 'name': 'Cat 2 Edit Invalid', 'description': 'Description modifiée' }
    with app.test_request_context():
        response_duplicate = admin_client.post(url_for('edit_category', category_id=category1_id), 
                                   data=invalid_data_duplicate, follow_redirects=False) 
    assert response_duplicate.status_code == 200 
    # CORRECTION BASÉE SUR CategoryForm.validate_name: raise ValidationError('Une catégorie avec ce nom existe déjà.')
    # Et la logique dans la route edit_category qui flashe "Une catégorie nommée '{new_name}' existe déjà."
    # La route edit_category vérifie l'unicité et flashe le message, le validateur du formulaire aussi.
    # Le message flash est généralement prioritaire pour l'affichage si la validation de la route intervient en premier.
    # Mais si le formulaire lui-même est invalidé par WTForms à cause de la validation d'unicité du champ, c'est le message du ValidationError du formulaire qui sera affiché près du champ.
    # Le code actuel dans app.py/edit_category flashe un message.
    # Le code actuel dans forms.py/CategoryForm/validate_name lève une ValidationError.
    # Généralement, le message flashé par la route est plus visible.
    # Cependant, si le validateur du formulaire est appelé (ce qui est le cas), c'est son message qui est pertinent.
    assert "Une catégorie avec ce nom existe déjà." in response_duplicate.data.decode('utf-8')


    with app.app_context():
        unchanged_category = db_session.get(Category, category1_id)
        assert unchanged_category.name == 'Cat 1 Edit Invalid' 

def test_edit_category_page_as_regular_user(regular_client, app, db_session):
    with app.app_context():
        test_category = Category(name='Catégorie Edit Regular Test', description='Desc test')
        db_session.add(test_category)
        db_session.commit()
        category_id = test_category.id

    with app.test_request_context():
        response = regular_client.get(url_for('edit_category', category_id=category_id))
    assert response.status_code == 403

def test_edit_category_submit_as_regular_user(regular_client, app, db_session):
    with app.app_context():
        test_category = Category(name='Catégorie Submit Regular Test', description='Desc test')
        db_session.add(test_category)
        db_session.commit()
        category_id = test_category.id

    updated_data = { 'name': 'Tentative Mod Regular', 'description': 'Tentative desc' }
    with app.test_request_context():
        response = regular_client.post(url_for('edit_category', category_id=category_id), data=updated_data)
    assert response.status_code == 403

def test_delete_empty_category_as_admin(admin_client, app, db_session):
    with app.app_context():
        empty_category = Category(name='Catégorie À Supprimer Vide', description='Test suppression')
        db_session.add(empty_category)
        db_session.commit()
        category_id = empty_category.id
        initial_count = db_session.query(Category).count()

    with app.test_request_context():
        response = admin_client.post(url_for('delete_category', category_id=category_id), 
                                   follow_redirects=True)
    assert response.status_code == 200
    assert "Catégorie supprimée avec succès !" in response.data.decode('utf-8')

    with app.app_context():
        assert db_session.query(Category).count() == initial_count - 1
        deleted_category = db_session.get(Category, category_id)
        assert deleted_category is None

def test_delete_category_with_products_as_admin(admin_client, app, db_session):
    with app.app_context():
        category_with_product = Category(name='Catégorie Avec Produit Test', description='Test non suppression')
        db_session.add(category_with_product)
        db_session.commit()
        
        test_product = Product(
            name='Produit Dans Cat Test', description='Desc produit test', price=Decimal('10.00'), unit="Unité", 
            quantity_in_stock=5, category_id=category_with_product.id
        )
        db_session.add(test_product)
        db_session.commit()
        
        category_id = category_with_product.id
        initial_category_count = db_session.query(Category).count()

    with app.test_request_context():
        response = admin_client.post(url_for('delete_category', category_id=category_id), 
                                   follow_redirects=True)
    assert response.status_code == 200
    assert "Cette catégorie contient des produits et ne peut pas être supprimée." in response.data.decode('utf-8') 
    
    with app.app_context():
        assert db_session.query(Category).count() == initial_category_count
        existing_category = db_session.get(Category, category_id)
        assert existing_category is not None

def test_delete_category_as_regular_user(regular_client, app, db_session):
    with app.app_context():
        test_category_del_reg = Category(name='Catégorie Delete Regular Test', description='Test')
        db_session.add(test_category_del_reg)
        db_session.commit()
        category_id = test_category_del_reg.id

    with app.test_request_context():
        response = regular_client.post(url_for('delete_category', category_id=category_id))
    assert response.status_code == 403

    with app.app_context():
        category_should_exist = db_session.get(Category, category_id)
        assert category_should_exist is not None