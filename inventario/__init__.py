from flask import Blueprint

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

def init_app(app):
    # Importar las rutas
    from . import inventario_routes
    # Importar los modelos
    from . import inventario_models
    
    # Registrar el blueprint
    app.register_blueprint(inventario_bp)
    
    # Inicializar la base de datos si es necesario
    with app.app_context():
        inventario_models.init_db()