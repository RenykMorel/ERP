from flask import Blueprint, jsonify

bp = Blueprint('reporting', __name__)

@bp.route('/reports', methods=['GET'])
def get_reports():
    # Implementa la lógica para generar reportes aquí
    return jsonify({"message": "Reports data"}), 200