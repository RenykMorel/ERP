from flask import jsonify, request, render_template, redirect, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from . import banco_bp
from .banco_models import NuevoBanco, Deposito, NotaCreditoBanco, NotaDebitoBanco, Transferencia, Conciliacion, Divisa
from extensions import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Rutas para Bancos
@banco_bp.route("/bancos")
@banco_bp.route("/Bancos")
@login_required
def sub_bancos():
    try:
        bancos = NuevoBanco.query.all()
        return render_template('banco/sub_bancos.html', bancos=bancos)
    except Exception as e:
        logger.error(f"Error al cargar la página de bancos: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de bancos: {str(e)}"}), 500

@banco_bp.route("/obtener-banco/<int:id>")
@login_required
def obtener_banco(id):
    try:
        banco = NuevoBanco.query.get_or_404(id)
        return jsonify(banco.to_dict())
    except Exception as e:
        logger.error(f"Error al obtener banco: {str(e)}")
        return jsonify({"error": f"Error al obtener banco: {str(e)}"}), 500

@banco_bp.route("/actualizar-banco/<int:id>", methods=["PUT"])
@login_required
def actualizar_banco(id):
    banco = NuevoBanco.query.get_or_404(id)
    datos = request.json
    campos_actualizables = ["nombre", "telefono", "contacto", "telefono_contacto", "estatus", "direccion", "codigo", "codigo_swift"]
    
    try:
        for key, value in datos.items():
            if key in campos_actualizables and value != getattr(banco, key):
                if key in ["nombre", "telefono"]:
                    existing = NuevoBanco.query.filter(NuevoBanco.id != id, getattr(NuevoBanco, key) == value).first()
                    if existing:
                        return jsonify({"error": f"Ya existe un banco con ese {key}"}), 400
                setattr(banco, key, value)
        
        db.session.commit()
        logger.info(f"Banco actualizado: {banco.nombre}")
        return jsonify(banco.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar banco: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/eliminar-banco/<int:id>", methods=["DELETE"])
@login_required
def eliminar_banco(id):
    banco = NuevoBanco.query.get_or_404(id)
    try:
        db.session.delete(banco)
        db.session.commit()
        logger.info(f"Banco eliminado: {banco.nombre}")
        return jsonify({"message": "Banco eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar banco: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/cambiar-estatus-banco/<int:id>", methods=["PUT"])
@login_required
def cambiar_estatus_banco(id):
    banco = NuevoBanco.query.get_or_404(id)
    datos = request.json
    try:
        banco.estatus = datos["estatus"]
        db.session.commit()
        logger.info(f"Estatus del banco {banco.nombre} cambiado a {banco.estatus}")
        return jsonify(banco.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al cambiar estatus del banco: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/buscar-bancos")
@login_required
def buscar_bancos():
    try:
        query = NuevoBanco.query
        if request.args.get("id"):
            query = query.filter(NuevoBanco.id == request.args.get("id"))
        if request.args.get("nombre"):
            query = query.filter(NuevoBanco.nombre.ilike(f"%{request.args.get('nombre')}%"))
        if request.args.get("contacto"):
            query = query.filter(NuevoBanco.contacto.ilike(f"%{request.args.get('contacto')}%"))
        if request.args.get("estatus"):
            query = query.filter(NuevoBanco.estatus == request.args.get("estatus"))

        bancos = query.all()
        logger.info(f"Búsqueda de bancos realizada. Resultados: {len(bancos)}")
        return jsonify([banco.to_dict() for banco in bancos])
    except Exception as e:
        logger.error(f"Error en buscar_bancos: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

from datetime import datetime

@banco_bp.route("/crear-banco", methods=["POST"])
@login_required
def crear_banco():
    datos = request.json
    logger.info(f"Datos recibidos para crear banco: {datos}")
    
    required_fields = ['nombre', 'telefono']
    for field in required_fields:
        if not datos.get(field):
            logger.warning(f"Campo requerido faltante: {field}")
            return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

    try:
        nuevo_banco = NuevoBanco(
            nombre=datos['nombre'],
            telefono=datos['telefono'],
            contacto=datos.get('contacto', ''),
            telefono_contacto=datos.get('telefono_contacto', ''),
            estatus=datos.get('estatus', 'activo'),
            direccion=datos.get('direccion', ''),
            codigo=datos.get('codigo', ''),
            codigo_swift=datos.get('codigo_swift', ''),
            fecha=datetime.now()  # Añade esta línea
        )
        logger.info(f"Objeto NuevoBanco creado: {vars(nuevo_banco)}")
        db.session.add(nuevo_banco)
        db.session.commit()
        logger.info(f"Nuevo banco creado: {nuevo_banco.nombre}")
        return jsonify({
            "message": "Banco creado exitosamente",
            "banco": nuevo_banco.to_dict()
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        error_info = str(e.orig)
        logger.error(f"IntegrityError al crear banco: {error_info}")
        if 'unique constraint' in error_info.lower():
            if 'nuevo_bancos_nombre_key' in error_info:
                mensaje = "Ya existe un banco con este nombre."
            elif 'nuevo_bancos_telefono_key' in error_info:
                mensaje = "Ya existe un banco con este número de teléfono."
            else:
                mensaje = "Ya existe un banco con información duplicada."
        else:
            mensaje = "Error de integridad al crear el banco."
        
        logger.warning(f"Error al crear banco: {mensaje} Detalles: {datos}")
        return jsonify({"error": mensaje}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error inesperado al crear banco: {str(e)}")
        return jsonify({"error": f"Error inesperado al crear el banco: {str(e)}"}), 500

@banco_bp.route("/eventos", methods=["GET"])
@login_required
def obtener_eventos():
    start = request.args.get('start')
    end = request.args.get('end')
    # Implementa la lógica de eventos aquí.
    return jsonify({"eventos": "Eventos encontrados"})

# Rutas para Notas de Crédito/Débito
@banco_bp.route("/notas-credito-debito")
@login_required
def notas_credito_debito():
    try:
        notas_credito = NotaCreditoBanco.query.all()
        notas_debito = NotaDebitoBanco.query.all()
        return render_template('banco/notas_credito_debito.html', notas_credito=notas_credito, notas_debito=notas_debito)
    except Exception as e:
        logger.error(f"Error al cargar la página de notas de crédito/débito: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de notas de crédito/débito: {str(e)}"}), 500

# Rutas para Transferencias Bancarias
@banco_bp.route("/transferencias")
@login_required
def transferencias():
    try:
        transferencias = Transferencia.query.all()
        return render_template('banco/transferencias.html', transferencias=transferencias)
    except Exception as e:
        logger.error(f"Error al cargar la página de transferencias: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de transferencias: {str(e)}"}), 500

# Rutas para Conciliación Bancaria
@banco_bp.route("/conciliacion")
@login_required
def conciliacion():
    try:
        conciliaciones = Conciliacion.query.all()
        return render_template('banco/conciliacion.html', conciliaciones=conciliaciones)
    except Exception as e:
        logger.error(f"Error al cargar la página de conciliación: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de conciliación: {str(e)}"}), 500

# Rutas para Divisas
@banco_bp.route("/divisas")
@login_required
def divisas():
    try:
        divisas = Divisa.query.all()
        return render_template('banco/divisas.html', divisas=divisas)
    except Exception as e:
        logger.error(f"Error al cargar la página de divisas: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de divisas: {str(e)}"}), 500

@banco_bp.route("/gestion-bancos")
@login_required
def gestion_bancos():
    try:
        bancos = NuevoBanco.query.all()
        return render_template('banco/gestion_bancos.html', bancos=bancos)
    except Exception as e:
        logger.error(f"Error al cargar la página de gestión de bancos: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de gestión de bancos: {str(e)}"}), 500