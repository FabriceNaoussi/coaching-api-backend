# Guide de déploiement — API Coaching Sportif

Ce guide décrit, étape par étape, comment cette API a été conteneurisée, déployée sur
Render, puis publiée sur RapidAPI. Les étapes correspondent à ce qui a réellement été
réalisé.

**API déployée :** https://coaching-api-backend-uo3x.onrender.com
**Page RapidAPI :** https://rapidapi.com/FabriceNaoussi/api/coaching-sportif

---

## 1. Prérequis

- Python 3.12 et les dépendances de `requirements.txt`
- Docker Desktop (pour tester l'image localement)
- Un compte GitHub (le dépôt doit y être publié)
- Un compte Render (https://render.com) — offre gratuite, sans carte de crédit
- Un compte RapidAPI (https://rapidapi.com) — gratuit en tant que fournisseur

## 2. Préparer l'application pour la production

Trois ajustements sont nécessaires dans `app.py` :

```python
import os
...
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
```

| Ajustement | Pourquoi |
|---|---|
| `host='0.0.0.0'` | À l'intérieur d'un conteneur, `127.0.0.1` désigne le conteneur lui-même. Avec cette valeur, l'application n'est pas joignable de l'extérieur (symptôme observé : « socket hang up »). `0.0.0.0` fait écouter sur toutes les interfaces réseau. |
| `PORT` lu depuis l'environnement | Render attribue dynamiquement le port. La valeur 5000 reste le défaut en local. |
| `debug=False` | Le mode debug expose un débogueur interactif et ne doit jamais être actif sur un serveur public. |

Fichiers requis à la racine du dépôt : `Dockerfile`, `requirements.txt`, `.dockerignore`,
`.gitignore` (qui exclut `.venv/`, `__pycache__/`, `.idea/`, `instance/` et `coaching.db`).

## 3. Tester l'image Docker localement

```bash
docker build -t coaching-api .
docker run -p 5000:5000 coaching-api
```

Vérification : une requête `POST http://127.0.0.1:5000/api/register` doit retourner `201`.
Le script `python client.py` permet aussi de tester toutes les routes d'un coup.

## 4. Publier le code sur GitHub

```bash
git init
git add .
git commit -m "Backend API coaching sportif"
gh repo create coaching-api-backend --public --source=. --remote=origin --push
```

## 5. Déployer sur Render

1. Se connecter sur https://render.com avec « Sign up with GitHub ».
2. **New + → Web Service**, puis sélectionner le dépôt `coaching-api-backend`.
3. Render détecte le `Dockerfile` automatiquement (langage : Docker).
4. Dans **Instance Type**, choisir **Free** (0 $/mois). L'option payante est sélectionnée
   par défaut : à vérifier avant de déployer.
5. Cliquer sur **Deploy web service**. La construction prend 2 à 5 minutes.
6. Les journaux se terminent par `Your service is live` et l'URL publique est affichée.

**Vérification :** `POST https://coaching-api-backend-uo3x.onrender.com/api/register` avec un
corps JSON valide doit retourner `201`. Un `GET /` retourne `404` : c'est normal, aucune
route n'est définie sur `/`.

**Redéploiement :** chaque `git push` sur la branche `master` redéploie automatiquement.

## 6. Publier sur RapidAPI

1. Se connecter sur https://rapidapi.com avec « Sign up with GitHub », puis ouvrir le
   **Provider Dashboard** (`rapidapi.com/provider`).
2. **Add New API** : nom `Coaching Sportif`, description courte, catégorie
   `Health and Fitness`.
3. Choisir **OpenAPI** et téléverser `docs/coaching-sportif-openapi.json` (fourni dans ce
   dépôt). Cette spécification décrit les 13 endpoints, l'authentification Bearer JWT
   et des exemples de requêtes/réponses.
4. Vérifier dans **API Specs → 1.0.0 → Settings → base URL** qu'**une seule** URL est
   configurée : celle de Render (et non `http://127.0.0.1:5000`).
5. Pour mettre à jour la définition plus tard : **Settings → Update your API → Upload
   an OpenAPI file** (écrase la définition existante).
6. Rendre l'API publique : onglet **Overview → Make your API public**, section
   **Danger Zone → API Visibility** : basculer de *Private* à *Public*, cocher la
   confirmation des conditions d'utilisation, puis sauvegarder.
7. Tester : **View in Hub → Run** sur `POST /api/register` avec un nouvel email : un
   `201` confirme que la chaîne complète fonctionne.

> Une première tentative d'import via une collection Postman avait produit des noms
> d'endpoints illisibles et une mauvaise URL de base. L'import d'une spécification OpenAPI
> écrit à la main a résolu ce problème et est la méthode recommandée.

## 7. Limites connues

| Limite | Conséquence | Piste d'amélioration |
|---|---|---|
| Base SQLite dans le conteneur | Les données sont **perdues** à chaque redémarrage/redéploiement sur Render | Migrer vers PostgreSQL (base managée) |
| `SECRET_KEY` écrite en dur dans `app.py` | À remplacer avant une vraie mise en production | La lire depuis une variable d'environnement |
| Service gratuit Render | S'endort après ~15 min d'inactivité ; le premier appel peut prendre 30 à 60 s | Offre payante ou appel de « réveil » |
| Limitation de requêtes absente du code | Aucun plafond appliqué côté serveur | Limiter par plan sur RapidAPI et/ou ajouter Flask-Limiter |
| Serveur de développement Flask | Non conçu pour la production | Utiliser Gunicorn dans le `Dockerfile` |
| Routes `Facture` et `Message` absentes | Les tables existent mais ne sont pas exposées | Ajouter des Blueprints sur le modèle de `routes_mesures.py` |

## 8. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `socket hang up` avec Docker | Flask écoute sur `127.0.0.1` | `host='0.0.0.0'` |
| Échec du déploiement sur Render | Port codé en dur | Lire `PORT` depuis l'environnement |
| Première requête très lente | Le service gratuit se réveille | Patienter, le timeout du client est à 60 s |
| `409` à l'inscription | Email déjà utilisé | Utiliser un autre email |
| `401` sur une route protégée | Token absent, invalide ou expiré (24 h) | Se reconnecter via `/api/login` |
| RapidAPI : « required fields missing » | Description ou type de média manquant sur un endpoint | Importer la spécification OpenAPI fournie |