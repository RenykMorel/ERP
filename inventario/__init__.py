from flask import Blueprint
from extensions import db
import logging

logger = logging.getLogger(__name__)

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

def init_app(app):
    def initialize_db():
        try:
            # Verificar que las tablas existen
            tables = ['items_inventario', 'movimientos_inventario', 'ajustes_inventario']
            for table in tables:
                if not db.engine.dialect.has_table(db.engine, table):
                    logger.error(f"Tabla {table} no existe!")
                    
            # Verificar que hay datos
            from .inventario_models import InventarioItem, MovimientoInventario
            items_count = InventarioItem.query.count()
            movimientos_count = MovimientoInventario.query.count()
            logger.info(f"Items en inventario: {items_count}")
            logger.info(f"Movimientos registrados: {movimientos_count}")
            
        except Exception as e:
            logger.error(f"Error al inicializar DB: {str(e)}")

    # Importar las rutas
    from . import inventario_routes
    # Importar los modelos
    from . import inventario_models
    
    # Registrar el blueprint
    app.register_blueprint(inventario_bp)
    
    # Inicializar la base de datos
    with app.app_context():
        inventario_models.init_db()
        initialize_db()