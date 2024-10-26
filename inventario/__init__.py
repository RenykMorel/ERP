from flask import Blueprint

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

def init_app(app):
    # Importamos las rutas aquí para evitar importaciones circulares
    app.register_blueprint(inventario_bp)

# Importamos las rutas después de crear el blueprint
from . import inventario_routes
from . import inventario_models