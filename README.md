# API Coaching Sportif — Vue Client

API REST développée en Python (Flask + SQLAlchemy) permettant à un client
de gérer son suivi avec son coach sportif : calendrier de séances,
progression (mesures), authentification sécurisée par JWT.

> Projet de session — Cours 420-A15-BB, Programmation de services.

## Technologies

- **Flask** — framework web Python
- **Flask-SQLAlchemy** — ORM pour la base de données relationnelle
- **PyJWT** — authentification par token
- **SQLite** — base de données (développement local)
- **pytest** — tests unitaires

## Installation

```bash
pip install -r requirements.txt
python app.py
```
Le serveur démarre sur `http://127.0.0.1:5000`.

## Authentification

Toutes les routes protégées attendent un en-tête HTTP :

Authorization:Bearer <token>
Le token est obtenu via `/api/login` et reste valide 24h.

## Endpoints

### Authentification

| Méthode | Route | Protégée | Description |
|---|---|---|---|
| POST | `/api/register` | Non | Créer un compte client |
| POST | `/api/login` | Non | Se connecter, obtenir un token JWT |
| GET | `/api/profil` | Oui | Obtenir les infos du client connecté |

**POST `/api/register`**
```json
// Requête
{
  "nom": "Alice Dupont",
  "email": "alice@example.com",
  "mot_de_passe": "motdepasse123",
  "plan_client": "basique",
  "objectif": "Perdre 5kg"
}
// Réponse 201
{ "message": "Compte créé", "client": { "id": 1, "nom": "Alice Dupont", ... } }
```

**POST `/api/login`**
```json
// Requête
{ "email": "alice@example.com", "mot_de_passe": "motdepasse123" }
// Réponse 200
{ "token": "eyJhbGci...", "client": { "id": 1, ... } }
```

### Séances (calendrier)

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/seances` | Lister toutes les séances du client connecté |
| GET | `/api/seances/<id>` | Détail d'une séance |
| POST | `/api/seances` | Créer une séance |
| PUT | `/api/seances/<id>/annuler` | Annuler une séance |
| PUT | `/api/seances/<id>/replanifier` | Proposer un nouvel horaire |

**POST `/api/seances`**
```json
{ "date": "2026-09-15T10:00:00", "type_exercice": "Musculation", "duree_minutes": 60 }
```

### Mesures (progression)

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/mesures` | Lister l'historique de mesures du client |
| POST | `/api/mesures` | Ajouter une mesure |
| DELETE | `/api/mesures/<id>` | Supprimer une mesure |

**POST `/api/mesures`**
```json
{ "poids": 78.5, "masse_grasse": 18.2 }
```

## Sécurité

- Mots de passe **hachés** (jamais stockés en clair) via `werkzeug.security`
- Authentification par **token JWT** signé, expirant après 24h
- **Isolation des données** : chaque requête filtre systématiquement par
  l'identifiant du client extrait du token — un client ne peut jamais
  accéder aux données d'un autre client (vérifié par test unitaire)

## Tests

```bash
pytest test_api.py -v
```

## Portée du projet (MVP)

Le modèle de données complet (5 tables : clients, séances, mesures,
factures, messages) est implémenté conformément à l'analyse fournie.
Pour ce projet, l'implémentation complète (API + client Android) se
concentre sur l'authentification, les séances et les mesures. Les
endpoints de facturation et de messagerie peuvent être ajoutés en
suivant le même patron (Blueprint + `token_requis`).