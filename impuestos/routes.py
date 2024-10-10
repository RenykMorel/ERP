from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from app import db
from .models import Formulario606, Formulario607, ReporteIT1, ImpuestoRenta, SerieFiscal, ConfiguracionesImpuestos
import logging

impuestos_bp = Blueprint('impuestos', __name__, url_prefix='/impuestos')

logger = logging.getLogger(__name__)

@impuestos_bp.route('/formulario606')
@login_required
def formulario606():
    try:
        registros = Formulario606.query.all()
        return render_template('impuestos/formulario606.html', registros=registros)
    except Exception as e:
        logger.error(f"Error al cargar el Formulario 606: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/formulario606/crear', methods=['GET', 'POST'])
@login_required
def crear_formulario606():
    if request.method == 'POST':
        # Lógica para crear un nuevo registro de Formulario 606
        pass
    return render_template('impuestos/crear_formulario606.html')

@impuestos_bp.route('/formulario607')
@login_required
def formulario607():
    try:
        registros = Formulario607.query.all()
        return render_template('impuestos/formulario607.html', registros=registros)
    except Exception as e:
        logger.error(f"Error al cargar el Formulario 607: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/formulario607/crear', methods=['GET', 'POST'])
@login_required
def crear_formulario607():
    if request.method == 'POST':
        # Lógica para crear un nuevo registro de Formulario 607
        pass
    return render_template('impuestos/crear_formulario607.html')

@impuestos_bp.route('/reporte-it1')
@login_required
def reporte_it1():
    try:
        reportes = ReporteIT1.query.all()
        return render_template('impuestos/reporte_it1.html', reportes=reportes)
    except Exception as e:
        logger.error(f"Error al cargar el Reporte IT1: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/reporte-it1/crear', methods=['GET', 'POST'])
@login_required
def crear_reporte_it1():
    if request.method == 'POST':
        # Lógica para crear un nuevo Reporte IT1
        pass
    return render_template('impuestos/crear_reporte_it1.html')

@impuestos_bp.route('/ir17')
@login_required
def ir17():
    try:
        declaraciones = ImpuestoRenta.query.all()
        return render_template('impuestos/ir17.html', declaraciones=declaraciones)
    except Exception as e:
        logger.error(f"Error al cargar el IR17: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/ir17/crear', methods=['GET', 'POST'])
@login_required
def crear_ir17():
    if request.method == 'POST':
        # Lógica para crear una nueva declaración IR17
        pass
    return render_template('impuestos/crear_ir17.html')

@impuestos_bp.route('/serie-fiscal')
@login_required
def serie_fiscal():
    try:
        series = SerieFiscal.query.all()
        return render_template('impuestos/serie_fiscal.html', series=series)
    except Exception as e:
        logger.error(f"Error al cargar las Series Fiscales: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/serie-fiscal/crear', methods=['GET', 'POST'])
@login_required
def crear_serie_fiscal():
    if request.method == 'POST':
        # Lógica para crear una nueva Serie Fiscal
        pass
    return render_template('impuestos/crear_serie_fiscal.html')

@impuestos_bp.route('/configuraciones')
@login_required
def configuraciones():
    try:
        # Intentamos obtener la configuración existente
        config = ConfiguracionesImpuestos.query.first()
        
        # Si no existe, creamos una nueva con valores por defecto
        if not config:
            config = ConfiguracionesImpuestos()
            db.session.add(config)
            db.session.commit()
        
        return render_template('impuestos/configuraciones.html', configuraciones=config)
    except Exception as e:
        logger.error(f"Error al cargar las Configuraciones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/configuraciones/guardar', methods=['POST'])
@login_required
def guardar_configuraciones():
    try:
        config = ConfiguracionesImpuestos.query.first()
        if not config:
            config = ConfiguracionesImpuestos()

        config.tasa_itbis = float(request.form['tasa_itbis'])
        config.tasa_isr_personas = float(request.form['tasa_isr_personas'])
        config.tasa_isr_empresas = float(request.form['tasa_isr_empresas'])
        config.limite_facturacion_606 = float(request.form['limite_facturacion_606'])

        db.session.add(config)
        db.session.commit()

        flash('Configuraciones guardadas exitosamente', 'success')
        return redirect(url_for('impuestos.configuraciones'))
    except Exception as e:
        logger.error(f"Error al guardar las Configuraciones: {str(e)}")
        flash('Error al guardar las configuraciones', 'error')
        return redirect(url_for('impuestos.configuraciones'))