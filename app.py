from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Client
from auth import generer_token, token_requis
from routes_seances import seances_bp
from routes_mesures import mesures_bp


def create_app(db_uri='sqlite:///coaching.db'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SECRET_KEY'] = 'change-moi-en-production'

    db.init_app(app)
    app.register_blueprint(seances_bp)
    app.register_blueprint(mesures_bp)

    with app.app_context():
        db.create_all()

    # --- Inscription ---
    @app.route('/api/register', methods=['POST'])
    def inscription():
        data = request.get_json()
        if Client.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Cet email est déjà utilisé'}), 409

        nouveau_client = Client(
            nom=data['nom'],
            email=data['email'],
            mot_de_passe_hash=generate_password_hash(data['mot_de_passe']),
            plan_client=data.get('plan_client', 'basique'),
            objectif=data.get('objectif', '')
        )
        db.session.add(nouveau_client)
        db.session.commit()
        return jsonify({'message': 'Compte créé', 'client': nouveau_client.to_dict()}), 201

    # --- Connexion ---
    @app.route('/api/login', methods=['POST'])
    def connexion():
        data = request.get_json()
        client = Client.query.filter_by(email=data['email']).first()

        if not client or not check_password_hash(client.mot_de_passe_hash, data['mot_de_passe']):
            return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

        token = generer_token(client.id)
        return jsonify({'token': token, 'client': client.to_dict()}), 200

    # --- Route protégée de test ---
    @app.route('/api/profil', methods=['GET'])
    @token_requis
    def profil(client_id_courant):
        client = Client.query.get(client_id_courant)
        return jsonify(client.to_dict()), 200

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000, host='0.0.0.0')