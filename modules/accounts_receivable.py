from flask import Blueprint, jsonify

bp = Blueprint('accounts_receivable', __name__)

@bp.route('/receivables', methods=['GET'])
def get_receivables():
    # Implementa la lógica para obtener las cuentas por cobrar aquí
    return jsonify({"message": "Accounts Receivable data"}), 200