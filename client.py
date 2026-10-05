import sys
import uuid
import requests


class ErreurClient(Exception):
    """Erreur de communication avec l'API (serveur injoignable, délai dépassé, etc.)."""
    pass


class CoachingClient:
    def __init__(self, base_url="http://127.0.0.1:5000", timeout=60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = None

    # --- Méthode centrale : toutes les requêtes passent par ici ---
    def _requete(self, methode, endpoint, json=None, auth=True):
        headers = {}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            reponse = requests.request(
                methode, self.base_url + endpoint,
                json=json, headers=headers, timeout=self.timeout
            )
        except requests.exceptions.ConnectionError:
            raise ErreurClient("Impossible de joindre le serveur (est-il démarré ?)")
        except requests.exceptions.Timeout:
            raise ErreurClient("Le serveur a mis trop de temps à répondre")
        except requests.exceptions.RequestException as e:
            raise ErreurClient(f"Erreur de communication : {e}")

        try:
            donnees = reponse.json()
        except ValueError:
            donnees = None  # réponse non JSON (ex. page d'erreur HTML)
        return reponse.status_code, donnees

    # --- Authentification ---
    def inscription(self, nom, email, mot_de_passe, objectif=""):
        return self._requete("POST", "/api/register", auth=False, json={
            "nom": nom, "email": email,
            "mot_de_passe": mot_de_passe, "objectif": objectif
        })

    def connexion(self, email, mot_de_passe):
        statut, donnees = self._requete("POST", "/api/login", auth=False, json={
            "email": email, "mot_de_passe": mot_de_passe
        })
        if statut == 200 and donnees:
            self.token = donnees["token"]
        return statut, donnees

    def profil(self):
        return self._requete("GET", "/api/profil")

    # --- Séances ---
    def creer_seance(self, date, type_exercice, duree_minutes):
        return self._requete("POST", "/api/seances", json={
            "date": date, "type_exercice": type_exercice, "duree_minutes": duree_minutes
        })

    def lister_seances(self):
        return self._requete("GET", "/api/seances")

    def obtenir_seance(self, seance_id):
        return self._requete("GET", f"/api/seances/{seance_id}")

    def annuler_seance(self, seance_id):
        return self._requete("PUT", f"/api/seances/{seance_id}/annuler")

    def replanifier_seance(self, seance_id, nouvelle_date):
        return self._requete("PUT", f"/api/seances/{seance_id}/replanifier",
                             json={"nouvelle_date": nouvelle_date})

    def supprimer_seance(self, seance_id):
        return self._requete("DELETE", f"/api/seances/{seance_id}")

    # --- Mesures ---
    def creer_mesure(self, poids, masse_grasse=None):
        corps = {"poids": poids}
        if masse_grasse is not None:
            corps["masse_grasse"] = masse_grasse
        return self._requete("POST", "/api/mesures", json=corps)

    def lister_mesures(self):
        return self._requete("GET", "/api/mesures")

    def modifier_mesure(self, mesure_id, poids=None, masse_grasse=None):
        corps = {}
        if poids is not None:
            corps["poids"] = poids
        if masse_grasse is not None:
            corps["masse_grasse"] = masse_grasse
        return self._requete("PUT", f"/api/mesures/{mesure_id}", json=corps)

    def supprimer_mesure(self, mesure_id):
        return self._requete("DELETE", f"/api/mesures/{mesure_id}")


def afficher(titre, resultat):
    statut, donnees = resultat
    print(f"[{statut}] {titre}")
    print(f"      {donnees}\n")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
    client = CoachingClient(url)
    email = f"client-{uuid.uuid4().hex[:8]}@example.com"  # email unique à chaque exécution

    try:
        print(f"=== Test de l'API : {url} ===\n")
        afficher("Inscription", client.inscription("Client Test", email, "motdepasse123", "Tester l'API"))
        afficher("Connexion", client.connexion(email, "motdepasse123"))
        afficher("Profil", client.profil())

        statut, seance = client.creer_seance("2026-10-05T08:00:00", "Course", 30)
        afficher("Créer une séance", (statut, seance))
        seance_id = seance["id"]

        afficher("Lister les séances", client.lister_seances())
        afficher("Détail de la séance", client.obtenir_seance(seance_id))
        afficher("Replanifier la séance", client.replanifier_seance(seance_id, "2026-10-06T09:00:00"))
        afficher("Annuler la séance", client.annuler_seance(seance_id))
        afficher("Supprimer la séance", client.supprimer_seance(seance_id))

        statut, mesure = client.creer_mesure(75.5, 18.0)
        afficher("Créer une mesure", (statut, mesure))
        afficher("Modifier la mesure", client.modifier_mesure(mesure["id"], poids=74.0))
        afficher("Lister les mesures", client.lister_mesures())
        afficher("Supprimer la mesure", client.supprimer_mesure(mesure["id"]))

        print("=== Test terminé ===")
    except ErreurClient as e:
        print(f"ERREUR : {e}")