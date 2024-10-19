from flask import Blueprint, request, jsonify

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    # Implementa la lógica de login aquí
    return jsonify({"message": "Login successful"}), 200

@bp.route('/logout', methods=['POST'])
def logout():
    # Implementa la lógica de logout aquí
    return jsonify({"message": "Logout successful"}), 200