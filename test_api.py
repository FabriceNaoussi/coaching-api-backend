import pytest
from app import create_app
from models import db


@pytest.fixture
def client():
    app = create_app('sqlite:///:memory:')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_inscription_reussie(client):
    reponse = client.post('/api/register', json={
        'nom': 'Alice',
        'email': 'alice@example.com',
        'mot_de_passe': 'motdepasse123'
    })
    assert reponse.status_code == 201
    assert reponse.get_json()['client']['nom'] == 'Alice'


def test_inscription_email_duplique(client):
    client.post('/api/register', json={
        'nom': 'Alice', 'email': 'alice@example.com', 'mot_de_passe': 'motdepasse123'
    })
    reponse = client.post('/api/register', json={
        'nom': 'Alice2', 'email': 'alice@example.com', 'mot_de_passe': 'autre'
    })
    assert reponse.status_code == 409


def test_connexion_reussie(client):
    client.post('/api/register', json={
        'nom': 'Bob', 'email': 'bob@example.com', 'mot_de_passe': 'secret123'
    })
    reponse = client.post('/api/login', json={
        'email': 'bob@example.com', 'mot_de_passe': 'secret123'
    })
    assert reponse.status_code == 200
    assert 'token' in reponse.get_json()


def test_connexion_mauvais_mot_de_passe(client):
    client.post('/api/register', json={
        'nom': 'Bob', 'email': 'bob@example.com', 'mot_de_passe': 'secret123'
    })
    reponse = client.post('/api/login', json={
        'email': 'bob@example.com', 'mot_de_passe': 'mauvais'
    })
    assert reponse.status_code == 401


def test_route_protegee_sans_token(client):
    reponse = client.get('/api/profil')
    assert reponse.status_code == 401


def test_creer_et_lister_seance(client):
    client.post('/api/register', json={
        'nom': 'Chloé', 'email': 'chloe@example.com', 'mot_de_passe': 'pass123'
    })
    token = client.post('/api/login', json={
        'email': 'chloe@example.com', 'mot_de_passe': 'pass123'
    }).get_json()['token']

    headers = {'Authorization': f'Bearer {token}'}
    reponse_creation = client.post('/api/seances', json={
        'date': '2026-10-01T09:00:00', 'type_exercice': 'Cardio', 'duree_minutes': 45
    }, headers=headers)
    assert reponse_creation.status_code == 201

    reponse_liste = client.get('/api/seances', headers=headers)
    assert reponse_liste.status_code == 200
    assert len(reponse_liste.get_json()['seances']) == 1


def test_isolation_entre_clients(client):
    # Chloé crée une séance
    client.post('/api/register', json={'nom': 'Chloé', 'email': 'chloe2@example.com', 'mot_de_passe': 'pass123'})
    token_chloe = client.post('/api/login', json={'email': 'chloe2@example.com', 'mot_de_passe': 'pass123'}).get_json()['token']
    client.post('/api/seances', json={'date': '2026-10-01T09:00:00', 'type_exercice': 'Cardio', 'duree_minutes': 45},
                headers={'Authorization': f'Bearer {token_chloe}'})

    # David se connecte et ne doit voir AUCUNE séance (pas celles de Chloé)
    client.post('/api/register', json={'nom': 'David', 'email': 'david@example.com', 'mot_de_passe': 'pass123'})
    token_david = client.post('/api/login', json={'email': 'david@example.com', 'mot_de_passe': 'pass123'}).get_json()['token']
    reponse = client.get('/api/seances', headers={'Authorization': f'Bearer {token_david}'})

    assert reponse.get_json()['seances'] == []