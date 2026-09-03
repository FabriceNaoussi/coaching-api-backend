from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    plan_client = db.Column(db.String(20), default='basique')  # basique | suivi_complet | premium
    objectif = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id, 'nom': self.nom, 'email': self.email,
            'plan_client': self.plan_client, 'objectif': self.objectif
        }


class Seance(db.Model):
    __tablename__ = 'seances'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    type_exercice = db.Column(db.String(100), nullable=False)
    duree_minutes = db.Column(db.Integer, nullable=False)
    statut = db.Column(db.String(30), default='confirmee')  # confirmee | en_attente_changement | annulee

    def to_dict(self):
        return {
            'id': self.id, 'client_id': self.client_id,
            'date': self.date.isoformat(), 'type_exercice': self.type_exercice,
            'duree_minutes': self.duree_minutes, 'statut': self.statut
        }


class Mesure(db.Model):
    __tablename__ = 'mesures'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    poids = db.Column(db.Float, nullable=False)
    masse_grasse = db.Column(db.Float)

    def to_dict(self):
        return {
            'id': self.id, 'client_id': self.client_id,
            'date': self.date.isoformat(), 'poids': self.poids,
            'masse_grasse': self.masse_grasse
        }


class Facture(db.Model):
    __tablename__ = 'factures'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    date_echeance = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(20), default='en_attente')  # payee | en_attente | en_retard

    def to_dict(self):
        return {
            'id': self.id, 'client_id': self.client_id, 'montant': self.montant,
            'date_echeance': self.date_echeance.isoformat(), 'statut': self.statut
        }


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    expediteur = db.Column(db.String(10), nullable=False)  # client | coach
    contenu = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'client_id': self.client_id, 'expediteur': self.expediteur,
            'contenu': self.contenu, 'date_envoi': self.date_envoi.isoformat()
        }