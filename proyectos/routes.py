from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app import db
from .models import Proyecto, Presupuesto, FacturacionProyecto
import logging

proyectos_bp = Blueprint('proyectos', __name__, url_prefix='/proyectos')

logger = logging.getLogger(__name__)

@proyectos_bp.route('/gestion')
@login_required
def gestion_proyectos():
    try:
        proyectos = Proyecto.query.all()
        return render_template('proyectos/gestion_proyectos.html', proyectos=proyectos)
    except Exception as e:
        logger.error(f"Error al cargar la página de gestión de proyectos: {str(e)}")
        return jsonify({"error": str(e)}), 500

@proyectos_bp.route('/presupuestos')
@login_required
def presupuestos():
    try:
        presupuestos = Presupuesto.query.all()
        return render_template('proyectos/presupuestos.html', presupuestos=presupuestos)
    except Exception as e:
        logger.error(f"Error al cargar la página de presupuestos: {str(e)}")
        return jsonify({"error": str(e)}), 500

@proyectos_bp.route('/facturacion')
@login_required
def facturacion():
    try:
        facturas = FacturacionProyecto.query.all()
        return render_template('proyectos/facturacion.html', facturas=facturas)
    except Exception as e:
        logger.error(f"Error al cargar la página de facturación por proyecto: {str(e)}")
        return jsonify({"error": str(e)}), 500

@proyectos_bp.route('/crear_proyecto', methods=['GET', 'POST'])
@login_required
def crear_proyecto():
    if request.method == 'POST':
        # Lógica para crear un nuevo proyecto
        pass
    return render_template('proyectos/crear_proyecto.html')

@proyectos_bp.route('/crear_presupuesto', methods=['GET', 'POST'])
@login_required
def crear_presupuesto():
    if request.method == 'POST':
        # Lógica para crear un nuevo presupuesto
        pass
    return render_template('proyectos/crear_presupuesto.html')

@proyectos_bp.route('/crear_factura', methods=['GET', 'POST'])
@login_required
def crear_factura():
    if request.method == 'POST':
        # Lógica para crear una nueva factura
        pass
    return render_template('proyectos/crear_factura.html')