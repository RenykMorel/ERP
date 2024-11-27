from flask import Blueprint, current_app
from extensions import db

facturacion_bp = Blueprint('facturacion', __name__)

def init_facturacion(app):
    """Inicializa componentes necesarios para el módulo de facturación"""
    with app.app_context():
        try:
            from .facturas_models import Vendedor
            
            vendedor = Vendedor.query.filter_by(codigo='V001').first()
            if not vendedor:
                vendedor = Vendedor(
                    codigo='V001',
                    nombre='Vendedor Principal',
                    activo=True,
                    telefono='000-000-0000',
                    email='vendedor.principal@empresa.com'
                )
                db.session.add(vendedor)
                db.session.commit()
                print("✓ Vendedor principal creado exitosamente")
            else:
                if not vendedor.activo:
                    vendedor.activo = True
                    db.session.commit()
                print("✓ Vendedor principal verificado")
        except Exception as e:
            print(f"✗ Error inicializando vendedor principal: {str(e)}")
            if db.session.is_active:
                db.session.rollback()

# Solo importar las rutas y modelos
from . import facturacion_routes
from . import facturas_models