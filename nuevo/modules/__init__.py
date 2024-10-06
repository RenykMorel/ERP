from flask import Blueprint

facturacion = Blueprint('facturacion', __name__, template_folder='templates', static_folder='static')

def init_app(app):
    from . import routes
    app.register_blueprint(facturacion, url_prefix='/facturacion')

# No importes las rutas aquí para evitar importaciones circulares