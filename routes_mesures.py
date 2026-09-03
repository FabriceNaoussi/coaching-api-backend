from datetime import datetime
from flask import Blueprint, request, jsonify
from models import db, Mesure
from auth import token_requis

mesures_bp = Blueprint('mesures', __name__)


# --- Lister toutes les mesures du client connecté (historique de progression) ---
@mesures_bp.route('/api/mesures', methods=['GET'])
@token_requis
def lister_mesures(client_id_courant):
    mesures = Mesure.query.filter_by(client_id=client_id_courant).order_by(Mesure.date).all()
    return jsonify({'mesures': [m.to_dict() for m in mesures]}), 200


# --- Ajouter une nouvelle mesure ---
@mesures_bp.route('/api/mesures', methods=['POST'])
@token_requis
def creer_mesure(client_id_courant):
    data = request.get_json()
    nouvelle_mesure = Mesure(
        client_id=client_id_courant,
        date=datetime.fromisoformat(data['date']) if 'date' in data else datetime.utcnow(),
        poids=data['poids'],
        masse_grasse=data.get('masse_grasse')
    )
    db.session.add(nouvelle_mesure)
    db.session.commit()
    return jsonify(nouvelle_mesure.to_dict()), 201


# --- Supprimer une mesure (ex: erreur de saisie) ---
@mesures_bp.route('/api/mesures/<int:mesure_id>', methods=['DELETE'])
@token_requis
def supprimer_mesure(client_id_courant, mesure_id):
    mesure = Mesure.query.filter_by(id=mesure_id, client_id=client_id_courant).first()
    if not mesure:
        return jsonify({'message': 'Mesure introuvable'}), 404
    db.session.delete(mesure)
    db.session.commit()
    return jsonify({'message': 'Mesure supprimée'}), 200