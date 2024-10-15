from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .models import Factura
from .forms import FacturaForm
from extensions import db
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime

# Configuración del blueprint
current_dir = os.path.dirname(os.path.abspath(__file__))

facturacion = Blueprint('facturacion', __name__, url_prefix='/facturacion')

@facturacion.route('/facturas')
@login_required
def facturas():
    return render_template('facturas.html')

@facturacion.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_factura():
    current_app.logger.info(f"Usuario {current_user.id} accediendo a la página de creación de factura")
    form = FacturaForm()
    if form.validate_on_submit():
        try:
            nueva_factura = Factura(
                numero=form.numero.data,
                cliente=form.cliente.data,
                fecha=form.fecha.data,
                total=form.total.data,
                estatus=form.estatus.data
            )
            db.session.add(nueva_factura)
            db.session.commit()
            flash('Factura creada exitosamente', 'success')
            return redirect(url_for('facturacion.facturas'))
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear factura: {str(e)}")
            flash('Error al crear la factura', 'error')
    return render_template('factura_form.html', form=form, title="Nueva Factura")

@facturacion.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_factura(id):
    current_app.logger.info(f"Usuario {current_user.id} accediendo a la edición de factura {id}")
    factura = Factura.query.get_or_404(id)
    form = FacturaForm(obj=factura)
    if form.validate_on_submit():
        try:
            form.populate_obj(factura)
            db.session.commit()
            flash('Factura actualizada exitosamente', 'success')
            return redirect(url_for('facturacion.facturas'))
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error al actualizar factura {id}: {str(e)}")
            flash('Error al actualizar la factura', 'error')
    return render_template('factura_form.html', form=form, factura=factura, title="Editar Factura")

@facturacion.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_factura(id):
    current_app.logger.info(f"Usuario {current_user.id} intentando eliminar la factura {id}")
    factura = Factura.query.get_or_404(id)
    try:
        db.session.delete(factura)
        db.session.commit()
        flash('Factura eliminada exitosamente', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar factura {id}: {str(e)}")
        flash('Error al eliminar la factura', 'error')
    return redirect(url_for('facturacion.facturas'))

@facturacion.route('/ver/<int:id>')
@login_required
def ver_factura(id):
    current_app.logger.info(f"Usuario {current_user.id} viendo detalles de la factura {id}")
    factura = Factura.query.get_or_404(id)
    return render_template('factura_detalle.html', factura=factura)

@facturacion.route('/api/submodulos')
@login_required
def get_submodulos():
    submodulos = ["Facturas", "Pre-facturas", "Notas de Crédito/Débito", "Reporte de Ventas", "Gestión de clientes"]
    return jsonify(submodulos)

@facturacion.route('/api/submodule-content/Facturas')
@login_required
def facturas_submodule():
    current_app.logger.info(f"Usuario {current_user.id} accediendo al submódulo de Facturas")
    try:
        content = render_template('facturas.html')
        return jsonify({
            "content": content,
            "script": "initializeFacturas();"
        })
    except Exception as e:
        current_app.logger.error(f"Error al renderizar facturas.html: {str(e)}")
        return jsonify({"error": "Error al cargar el contenido del submódulo"}), 500

@facturacion.route('/api/facturas')
@login_required
def api_facturas():
    current_app.logger.info(f"Usuario {current_user.id} solicitando lista de facturas vía API")
    facturas = Factura.query.all()
    return jsonify([{
        'id': f.id,
        'numero': f.numero,
        'cliente': f.cliente,
        'fecha': f.fecha.isoformat(),
        'total': f.total,
        'estatus': f.estatus
    } for f in facturas])

@facturacion.route('/api/crear', methods=['POST'])
@login_required
def api_crear_factura():
    current_app.logger.info(f"Usuario {current_user.id} intentando crear factura vía API")
    data = request.json
    try:
        nueva_factura = Factura(
            numero=data['numero'],
            cliente=data['cliente'],
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
            total=data['total'],
            estatus=data['estatus']
        )
        db.session.add(nueva_factura)
        db.session.commit()
        return jsonify({"success": True, "message": "Factura creada exitosamente"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error al crear factura vía API: {str(e)}")
        return jsonify({"success": False, "message": "Error al crear la factura"}), 500

@facturacion.route('/api/editar/<int:id>', methods=['PUT'])
@login_required
def api_editar_factura(id):
    current_app.logger.info(f"Usuario {current_user.id} intentando editar factura {id} vía API")
    factura = Factura.query.get_or_404(id)
    data = request.json
    try:
        factura.numero = data['numero']
        factura.cliente = data['cliente']
        factura.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        factura.total = data['total']
        factura.estatus = data['estatus']
        db.session.commit()
        return jsonify({"success": True, "message": "Factura actualizada exitosamente"})
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error al actualizar factura {id} vía API: {str(e)}")
        return jsonify({"success": False, "message": "Error al actualizar la factura"}), 500

@facturacion.route('/api/eliminar/<int:id>', methods=['DELETE'])
@login_required
def api_eliminar_factura(id):
    current_app.logger.info(f"Usuario {current_user.id} intentando eliminar factura {id} vía API")
    factura = Factura.query.get_or_404(id)
    try:
        db.session.delete(factura)
        db.session.commit()
        return jsonify({"success": True, "message": "Factura eliminada exitosamente"})
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar factura {id} vía API: {str(e)}")
        return jsonify({"success": False, "message": "Error al eliminar la factura"}), 500

# Manejador de errores para el blueprint
@facturacion.errorhandler(404)
def handle_404(e):
    return jsonify(error=str(e)), 404

@facturacion.errorhandler(500)
def handle_500(e):
    current_app.logger.error(f'Error del servidor: {str(e)}')
    return jsonify(error='Error interno del servidor'), 500