
from flask import Blueprint

facturacion_bp = Blueprint('facturacion', __name__)

from . import facturacion_routes
from . import facturas_models
