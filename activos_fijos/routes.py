from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required
from extensions import db
from .models import ActivoFijo, Depreciacion, Retiro, Revalorizacion, TipoActivoFijo
import logging

activos_fijos_bp = Blueprint('activos_fijos', __name__, url_prefix='/activos_fijos')

logger = logging.getLogger(__name__)

@activos_fijos_bp.route('/activo_fijo')
@login_required
def activo_fijo():
    try:
        activos = ActivoFijo.query.all()
        return render_template('activos_fijos/activo_fijo.html', activos=activos)
    except Exception as e:
        logger.error(f"Error al cargar la página de activos fijos: {str(e)}")
        return jsonify({"error": str(e)}), 500

@activos_fijos_bp.route('/crear_activo_fijo', methods=['GET', 'POST'])
@login_required
def crear_activo_fijo():
    # Lógica para crear un nuevo activo fijo
    return render_template('activos_fijos/crear_activo_fijo.html')

@activos_fijos_bp.route('/depreciacion')
@login_required
def depreciacion():
    try:
        depreciaciones = Depreciacion.query.all()
        return render_template('activos_fijos/depreciacion.html', depreciaciones=depreciaciones)
    except Exception as e:
        logger.error(f"Error al cargar la página de depreciaciones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@activos_fijos_bp.route('/calcular_depreciacion', methods=['GET', 'POST'])
@login_required
def calcular_depreciacion():
    # Lógica para calcular la depreciación
    return render_template('activos_fijos/calcular_depreciacion.html')

@activos_fijos_bp.route('/retiro')
@login_required
def retiro():
    try:
        retiros = Retiro.query.all()
        return render_template('activos_fijos/retiro.html', retiros=retiros)
    except Exception as e:
        logger.error(f"Error al cargar la página de retiros: {str(e)}")
        return jsonify({"error": str(e)}), 500

@activos_fijos_bp.route('/registrar_retiro', methods=['GET', 'POST'])
@login_required
def registrar_retiro():
    # Lógica para registrar un retiro
    return render_template('activos_fijos/registrar_retiro.html')

@activos_fijos_bp.route('/revalorizacion')
@login_required
def revalorizacion():
    try:
        revalorizaciones = Revalorizacion.query.all()
        return render_template('activos_fijos/revalorizacion.html', revalorizaciones=revalorizaciones)
    except Exception as e:
        logger.error(f"Error al cargar la página de revalorizaciones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@activos_fijos_bp.route('/registrar_revalorizacion', methods=['GET', 'POST'])
@login_required
def registrar_revalorizacion():
    # Lógica para registrar una revalorización
    return render_template('activos_fijos/registrar_revalorizacion.html')

@activos_fijos_bp.route('/tipo_activo_fijo')
@login_required
def tipo_activo_fijo():
    try:
        tipos = TipoActivoFijo.query.all()
        return render_template('activos_fijos/tipo_activo_fijo.html', tipos_activo_fijo=tipos)
    except Exception as e:
        logger.error(f"Error al cargar la página de tipos de activo fijo: {str(e)}")
        return jsonify({"error": str(e)}), 500

@activos_fijos_bp.route('/crear_tipo_activo_fijo', methods=['GET', 'POST'])
@login_required
def crear_tipo_activo_fijo():
    # Lógica para crear un nuevo tipo de activo fijo
    return render_template('activos_fijos/crear_tipo_activo_fijo.html')