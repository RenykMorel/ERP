from flask import Blueprint

compras_bp = Blueprint('compras', __name__)

from . import routes