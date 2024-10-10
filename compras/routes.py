from flask import jsonify, request, render_template, redirect, url_for
from flask_login import login_required
from . import compras_bp
from .models import SolicitudCompra, OrdenCompra, RecepcionMateriales, Gasto
from extensions import db
import logging

logger = logging.getLogger(__name__)

# Rutas para Solicitudes de Compra
@compras_bp.route("/solicitudes")
@compras_bp.route("/Solicitudes")
@login_required
def solicitudes_compra():
    try:
        solicitudes = SolicitudCompra.query.all()
        return render_template('compras/solicitudes_compra.html', solicitudes=solicitudes)
    except Exception as e:
        logger.error(f"Error al cargar la página de solicitudes de compra: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de solicitudes de compra: {str(e)}"}), 500

@compras_bp.route("/crear-solicitud", methods=["GET", "POST"])
@login_required
def crear_solicitud():
    if request.method == "POST":
        datos = request.form
        try:
            nueva_solicitud = SolicitudCompra(
                descripcion=datos['descripcion'],
                estado='Pendiente'
            )
            db.session.add(nueva_solicitud)
            db.session.commit()
            logger.info(f"Nueva solicitud de compra creada: {nueva_solicitud.id}")
            return redirect(url_for('compras.solicitudes_compra'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear solicitud de compra: {str(e)}")
            return jsonify({"error": "Error al crear la solicitud de compra."}), 500
    return render_template('compras/crear_solicitud.html')

# Rutas para Órdenes de Compra
@compras_bp.route("/ordenes")
@compras_bp.route("/Ordenes")
@login_required
def ordenes_compra():
    try:
        ordenes = OrdenCompra.query.all()
        return render_template('compras/ordenes_compra.html', ordenes=ordenes)
    except Exception as e:
        logger.error(f"Error al cargar la página de órdenes de compra: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de órdenes de compra: {str(e)}"}), 500

@compras_bp.route("/crear-orden", methods=["GET", "POST"])
@login_required
def crear_orden():
    if request.method == "POST":
        datos = request.form
        try:
            nueva_orden = OrdenCompra(
                proveedor=datos['proveedor'],
                total=float(datos['total']),
                estado='Pendiente'
            )
            db.session.add(nueva_orden)
            db.session.commit()
            logger.info(f"Nueva orden de compra creada: {nueva_orden.id}")
            return redirect(url_for('compras.ordenes_compra'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear orden de compra: {str(e)}")
            return jsonify({"error": "Error al crear la orden de compra."}), 500
    return render_template('compras/crear_orden.html')

# Rutas para Recepción de Materiales
@compras_bp.route("/recepcion")
@compras_bp.route("/Recepcion")
@login_required
def recepcion_materiales():
    try:
        recepciones = RecepcionMateriales.query.all()
        return render_template('compras/recepcion_materiales.html', recepciones=recepciones)
    except Exception as e:
        logger.error(f"Error al cargar la página de recepción de materiales: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de recepción de materiales: {str(e)}"}), 500

@compras_bp.route("/crear-recepcion", methods=["GET", "POST"])
@login_required
def crear_recepcion():
    if request.method == "POST":
        datos = request.form
        try:
            nueva_recepcion = RecepcionMateriales(
                orden_compra_id=datos['orden_compra_id'],
                fecha_recepcion=datos['fecha_recepcion'],
                estado='Recibido'
            )
            db.session.add(nueva_recepcion)
            db.session.commit()
            logger.info(f"Nueva recepción de materiales creada: {nueva_recepcion.id}")
            return redirect(url_for('compras.recepcion_materiales'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear recepción de materiales: {str(e)}")
            return jsonify({"error": "Error al crear la recepción de materiales."}), 500
    return render_template('compras/crear_recepcion.html')

# Rutas para Gastos
@compras_bp.route("/gastos")
@compras_bp.route("/Gastos")
@login_required
def gastos():
    try:
        gastos = Gasto.query.all()
        return render_template('compras/gastos.html', gastos=gastos)
    except Exception as e:
        logger.error(f"Error al cargar la página de gastos: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de gastos: {str(e)}"}), 500

@compras_bp.route("/crear-gasto", methods=["GET", "POST"])
@login_required
def crear_gasto():
    if request.method == "POST":
        datos = request.form
        try:
            nuevo_gasto = Gasto(
                descripcion=datos['descripcion'],
                monto=float(datos['monto']),
                fecha=datos['fecha'],
                categoria=datos['categoria']
            )
            db.session.add(nuevo_gasto)
            db.session.commit()
            logger.info(f"Nuevo gasto creado: {nuevo_gasto.id}")
            return redirect(url_for('compras.gastos'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear gasto: {str(e)}")
            return jsonify({"error": "Error al crear el gasto."}), 500
    return render_template('compras/crear_gasto.html')

# Ruta para el Reporte de Compras y Gastos
@compras_bp.route("/reporte")
@login_required
def reporte():
    try:
        compras = OrdenCompra.query.all()
        gastos = Gasto.query.all()
        total_compras = sum(compra.total for compra in compras)
        total_gastos = sum(gasto.monto for gasto in gastos)
        return render_template('compras/reporte_compras.html',  # Nombre actualizado
                               compras=compras, 
                               gastos=gastos, 
                               total_compras=total_compras, 
                               total_gastos=total_gastos)
    except Exception as e:
        logger.error(f"Error al generar el reporte de compras y gastos: {str(e)}")
        return jsonify({"error": f"Error al generar el reporte de compras y gastos: {str(e)}"}), 500