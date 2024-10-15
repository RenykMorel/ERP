from flask import Blueprint

banco_bp = Blueprint('banco', __name__)

from . import routes