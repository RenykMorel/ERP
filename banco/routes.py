from flask import jsonify, request, render_template
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from . import banco_bp
from banco_models import Banco
from extensions import db
import logging

logger = logging.getLogger(__name__)

@banco_bp.route("/bancos")
@banco_bp.route("/Bancos")
@login_required
def sub_bancos():
    try:
        bancos = Banco.query.all()
        return render_template('sub_bancos.html', bancos=bancos)
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error al cargar la página de bancos: {error_message}")
        return jsonify({"error": f"Error al cargar la página de bancos: {error_message}"}), 500

@banco_bp.route("/obtener-banco/<int:id>")
@login_required
def obtener_banco(id):
    banco = Banco.query.get_or_404(id)
    return jsonify(banco.to_dict())

@banco_bp.route("/actualizar-banco/<int:id>", methods=["PUT"])
@login_required
def actualizar_banco(id):
    banco = Banco.query.get_or_404(id)
    datos = request.json
    campos_actualizables = ["nombre", "telefono", "contacto", "telefono_contacto", "estatus"]
    
    try:
        for key, value in datos.items():
            if key in campos_actualizables and value != getattr(banco, key):
                if key in ["nombre", "telefono"]:
                    existing = Banco.query.filter(Banco.id != id, getattr(Banco, key) == value).first()
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
    banco = Banco.query.get_or_404(id)
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
    banco = Banco.query.get_or_404(id)
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
        query = Banco.query
        if request.args.get("id"):
            query = query.filter(Banco.id == request.args.get("id"))
        if request.args.get("nombre"):
            query = query.filter(Banco.nombre.ilike(f"%{request.args.get('nombre')}%"))
        if request.args.get("contacto"):
            query = query.filter(Banco.contacto.ilike(f"%{request.args.get('contacto')}%"))
        if request.args.get("estatus"):
            query = query.filter(Banco.estatus == request.args.get("estatus"))

        bancos = query.all()
        logger.info(f"Búsqueda de bancos realizada. Resultados: {len(bancos)}")
        return jsonify([banco.to_dict() for banco in bancos])
    except Exception as e:
        logger.error(f"Error en buscar_bancos: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@banco_bp.route("/crear-banco", methods=["POST"])
@login_required
def crear_banco():
    datos = request.json
    try:
        nuevo_banco = Banco(
            nombre=datos['nombre'],
            telefono=datos['telefono'],
            contacto=datos['contacto'],
            telefono_contacto=datos['telefono_contacto'],
            estatus=datos.get('estatus', 'activo')
        )
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
        if 'duplicate key value violates unique constraint' in error_info:
            if 'banco_nombre_key' in error_info:
                mensaje = "Ya existe un banco con este nombre."
            elif 'banco_telefono_key' in error_info:
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
        return jsonify({"error": "Error inesperado al crear el banco."}), 500