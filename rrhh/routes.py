from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required
from .models import Empleado, Nomina, EvaluacionDesempeno
from app import db
import logging

rrhh_bp = Blueprint('rrhh', __name__, url_prefix='/rrhh')

logger = logging.getLogger(__name__)

@rrhh_bp.route('/empleados')
@login_required
def empleados():
    try:
        empleados = Empleado.query.all()
        return render_template('rrhh/empleados.html', empleados=empleados)
    except Exception as e:
        logger.error(f"Error al cargar la página de empleados: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de empleados: {str(e)}"}), 500

@rrhh_bp.route('/empleados/crear', methods=['GET', 'POST'])
@login_required
def crear_empleado():
    if request.method == 'POST':
        # Lógica para crear un empleado
        pass
    return render_template('rrhh/crear_empleado.html')

@rrhh_bp.route('/nomina')
@login_required
def nomina():
    try:
        nominas = Nomina.query.all()
        return render_template('rrhh/nomina.html', nominas=nominas)
    except Exception as e:
        logger.error(f"Error al cargar la página de nómina: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de nómina: {str(e)}"}), 500

@rrhh_bp.route('/nomina/crear', methods=['GET', 'POST'])
@login_required
def crear_nomina():
    if request.method == 'POST':
        # Lógica para crear una nómina
        pass
    return render_template('rrhh/crear_nomina.html')

@rrhh_bp.route('/evaluacion')
@login_required
def evaluacion():
    try:
        evaluaciones = EvaluacionDesempeno.query.all()
        return render_template('rrhh/evaluacion.html', evaluaciones=evaluaciones)
    except Exception as e:
        logger.error(f"Error al cargar la página de evaluación de desempeño: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de evaluación de desempeño: {str(e)}"}), 500

@rrhh_bp.route('/evaluacion/crear', methods=['GET', 'POST'])
@login_required
def crear_evaluacion():
    if request.method == 'POST':
        # Lógica para crear una evaluación
        pass
    return render_template('rrhh/crear_evaluacion.html')