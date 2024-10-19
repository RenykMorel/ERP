from flask import Blueprint, jsonify

bp = Blueprint('inventory', __name__)

@bp.route('/inventory', methods=['GET'])
def get_inventory():
    # Implementa la lógica para obtener el inventario aquí
    return jsonify({"message": "Inventory data"}), 200