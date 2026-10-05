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

# ---------- Fonctions utilitaires ----------

def creer_client_connecte(client, email, nom="Test"):
    """Inscrit un client, le connecte, et retourne les en-têtes d'authentification."""
    client.post('/api/register', json={'nom': nom, 'email': email, 'mot_de_passe': 'pass123'})
    token = client.post('/api/login', json={
        'email': email, 'mot_de_passe': 'pass123'
    }).get_json()['token']
    return {'Authorization': f'Bearer {token}'}


def creer_seance(client, headers):
    return client.post('/api/seances', json={
        'date': '2026-10-01T09:00:00', 'type_exercice': 'Cardio', 'duree_minutes': 45
    }, headers=headers).get_json()


# ---------- Authentification ----------

def test_profil_avec_token_valide(client):
    headers = creer_client_connecte(client, 'profil@example.com', nom='Alice')
    reponse = client.get('/api/profil', headers=headers)
    assert reponse.status_code == 200
    assert reponse.get_json()['email'] == 'profil@example.com'


def test_token_invalide_refuse(client):
    reponse = client.get('/api/profil', headers={'Authorization': 'Bearer abc.def.ghi'})
    assert reponse.status_code == 401


# ---------- Séances ----------

def test_detail_seance(client):
    headers = creer_client_connecte(client, 'detail@example.com')
    seance = creer_seance(client, headers)
    reponse = client.get(f"/api/seances/{seance['id']}", headers=headers)
    assert reponse.status_code == 200
    assert reponse.get_json()['type_exercice'] == 'Cardio'


def test_detail_seance_inexistante(client):
    headers = creer_client_connecte(client, 'inexistante@example.com')
    reponse = client.get('/api/seances/999', headers=headers)
    assert reponse.status_code == 404


def test_detail_seance_autre_client_refuse(client):
    headers_a = creer_client_connecte(client, 'a@example.com')
    seance = creer_seance(client, headers_a)
    headers_b = creer_client_connecte(client, 'b@example.com')
    reponse = client.get(f"/api/seances/{seance['id']}", headers=headers_b)
    assert reponse.status_code == 404


def test_annuler_seance(client):
    headers = creer_client_connecte(client, 'annuler@example.com')
    seance = creer_seance(client, headers)
    reponse = client.put(f"/api/seances/{seance['id']}/annuler", headers=headers)
    assert reponse.status_code == 200
    assert reponse.get_json()['statut'] == 'annulee'


def test_annuler_seance_autre_client_refuse(client):
    headers_a = creer_client_connecte(client, 'a2@example.com')
    seance = creer_seance(client, headers_a)
    headers_b = creer_client_connecte(client, 'b2@example.com')
    reponse = client.put(f"/api/seances/{seance['id']}/annuler", headers=headers_b)
    assert reponse.status_code == 404


def test_replanifier_seance(client):
    headers = creer_client_connecte(client, 'replan@example.com')
    seance = creer_seance(client, headers)
    reponse = client.put(f"/api/seances/{seance['id']}/replanifier",
                         json={'nouvelle_date': '2026-10-05T14:00:00'}, headers=headers)
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps['statut'] == 'en_attente_changement'
    assert corps['date'] == '2026-10-05T14:00:00'


# ---------- Mesures ----------

def test_mesures_sans_token_refusees(client):
    assert client.get('/api/mesures').status_code == 401


def test_creer_et_lister_mesures(client):
    headers = creer_client_connecte(client, 'mesures@example.com')
    reponse_creation = client.post('/api/mesures', json={
        'poids': 75.5, 'masse_grasse': 18.0
    }, headers=headers)
    assert reponse_creation.status_code == 201

    reponse_liste = client.get('/api/mesures', headers=headers)
    assert reponse_liste.status_code == 200
    mesures = reponse_liste.get_json()['mesures']
    assert len(mesures) == 1
    assert mesures[0]['poids'] == 75.5


def test_supprimer_mesure(client):
    headers = creer_client_connecte(client, 'suppr@example.com')
    mesure = client.post('/api/mesures', json={'poids': 80}, headers=headers).get_json()
    reponse = client.delete(f"/api/mesures/{mesure['id']}", headers=headers)
    assert reponse.status_code == 200
    assert client.get('/api/mesures', headers=headers).get_json()['mesures'] == []


def test_supprimer_mesure_autre_client_refuse(client):
    headers_a = creer_client_connecte(client, 'a3@example.com')
    mesure = client.post('/api/mesures', json={'poids': 70}, headers=headers_a).get_json()
    headers_b = creer_client_connecte(client, 'b3@example.com')
    reponse = client.delete(f"/api/mesures/{mesure['id']}", headers=headers_b)
    assert reponse.status_code == 404
    # la mesure de A existe toujours
    assert len(client.get('/api/mesures', headers=headers_a).get_json()['mesures']) == 1