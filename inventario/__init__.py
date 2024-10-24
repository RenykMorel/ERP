
from flask import Blueprint

inventario_bp = Blueprint('inventario', __name__)

def init_app(app):
    # Inicialización específica para el módulo de inventario
    pass

from . import inventario_models
from . import inventario_routes