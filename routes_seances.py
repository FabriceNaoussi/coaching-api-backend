from datetime import datetime
from flask import Blueprint, request, jsonify
from models import db, Seance
from auth import token_requis

seances_bp = Blueprint('seances', __name__)


# --- Lister toutes les séances du client connecté ---
@seances_bp.route('/api/seances', methods=['GET'])
@token_requis
def lister_seances(client_id_courant):
    seances = Seance.query.filter_by(client_id=client_id_courant).order_by(Seance.date).all()
    return jsonify({'seances': [s.to_dict() for s in seances]}), 200


# --- Détail d'une séance précise ---
@seances_bp.route('/api/seances/<int:seance_id>', methods=['GET'])
@token_requis
def obtenir_seance(client_id_courant, seance_id):
    seance = Seance.query.filter_by(id=seance_id, client_id=client_id_courant).first()
    if not seance:
        return jsonify({'message': 'Séance introuvable'}), 404
    return jsonify(seance.to_dict()), 200


# --- Créer une nouvelle séance ---
@seances_bp.route('/api/seances', methods=['POST'])
@token_requis
def creer_seance(client_id_courant):
    data = request.get_json()
    nouvelle_seance = Seance(
        client_id=client_id_courant,
        date=datetime.fromisoformat(data['date']),
        type_exercice=data['type_exercice'],
        duree_minutes=data['duree_minutes'],
        statut='confirmee'
    )
    db.session.add(nouvelle_seance)
    db.session.commit()
    return jsonify(nouvelle_seance.to_dict()), 201


# --- Annuler une séance ---
@seances_bp.route('/api/seances/<int:seance_id>/annuler', methods=['PUT'])
@token_requis
def annuler_seance(client_id_courant, seance_id):
    seance = Seance.query.filter_by(id=seance_id, client_id=client_id_courant).first()
    if not seance:
        return jsonify({'message': 'Séance introuvable'}), 404
    seance.statut = 'annulee'
    db.session.commit()
    return jsonify(seance.to_dict()), 200


# --- Proposer un changement d'horaire (replanifier) ---
@seances_bp.route('/api/seances/<int:seance_id>/replanifier', methods=['PUT'])
@token_requis
def replanifier_seance(client_id_courant, seance_id):
    seance = Seance.query.filter_by(id=seance_id, client_id=client_id_courant).first()
    if not seance:
        return jsonify({'message': 'Séance introuvable'}), 404
    data = request.get_json()
    seance.date = datetime.fromisoformat(data['nouvelle_date'])
    seance.statut = 'en_attente_changement'
    db.session.commit()
    return jsonify(seance.to_dict()), 200

# --- Supprimer une séance ---
@seances_bp.route('/api/seances/<int:seance_id>', methods=['DELETE'])
@token_requis
def supprimer_seance(client_id_courant, seance_id):
    seance = Seance.query.filter_by(id=seance_id, client_id=client_id_courant).first()
    if not seance:
        return jsonify({'message': 'Séance introuvable'}), 404
    db.session.delete(seance)
    db.session.commit()
    return jsonify({'message': 'Séance supprimée'}), 200