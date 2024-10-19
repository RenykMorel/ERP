from flask import Blueprint, jsonify

bp = Blueprint('accounts_payable', __name__)

@bp.route('/payables', methods=['GET'])
def get_payables():
    # Implementa la lógica para obtener las cuentas por pagar aquí
    return jsonify({"message": "Accounts Payable data"}), 200