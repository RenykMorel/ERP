from flask import Blueprint, jsonify

bp = Blueprint('general_ledger', __name__)

@bp.route('/ledger', methods=['GET'])
def get_ledger():
    # Implementa la lógica para obtener el libro mayor aquí
    return jsonify({"message": "General Ledger data"}), 200