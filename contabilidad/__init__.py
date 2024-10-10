from flask import Blueprint

contabilidad_bp = Blueprint('contabilidad', __name__)

from . import routes