from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from .asistente import AsistenteVirtual, Conversacion, ContextoAsistente
from extensions import db

asistente_bp = Blueprint('asistente', __name__)

@asistente_bp.route('/api/asistente', methods=['POST'])
@login_required
def consultar_asistente():
    if not current_app.config.get('ASISTENTE_ACTIVO', False) or not current_user.asistente_activo:
        return jsonify({"respuesta": "El asistente no está activo para tu usuario. Contacta al administrador."}), 403

    data = request.json
    pregunta = data.get('pregunta', '').strip()
    usuario_id = current_user.id
    pagina_actual = data.get('pagina_actual', '')

    if not pregunta:
        return jsonify({"respuesta": "Por favor, proporciona una pregunta."}), 400

    try:
        asistente = AsistenteVirtual()
        respuesta = asistente.responder(pregunta, usuario_id, pagina_actual)

        # Guardar la conversación en la base de datos
        nueva_conversacion = Conversacion(usuario_id=usuario_id, contenido=f"Usuario: {pregunta}\nAsistente: {respuesta['contenido']}")
        db.session.add(nueva_conversacion)
        db.session.commit()

        return jsonify(respuesta)
    except Exception as e:
        current_app.logger.error(f"Error al consultar el asistente: {str(e)}")
        return jsonify({"tipo": "texto", "respuesta": "Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde."}), 500

@asistente_bp.route('/api/asistente_status')
@login_required
def asistente_status():
    try:
        asistente_activo = current_app.config.get('ASISTENTE_ACTIVO', False)
        return jsonify({
            "activo": current_user.asistente_activo and asistente_activo
        })
    except Exception as e:
        current_app.logger.error(f"Error al obtener el estado del asistente: {str(e)}")
        return jsonify({"error": "Error al obtener el estado del asistente"}), 500

@asistente_bp.route('/api/actualizar_estado_asistente', methods=['POST'])
@login_required
def actualizar_estado_asistente():
    if current_user.rol != 'admin':
        return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403

    try:
        nuevo_estado = request.json.get('activo', False)
        current_app.config['ASISTENTE_ACTIVO'] = nuevo_estado
        return jsonify({"mensaje": "Estado del asistente actualizado correctamente"})
    except Exception as e:
        current_app.logger.error(f"Error al actualizar el estado del asistente: {str(e)}")
        return jsonify({"error": "Error al actualizar el estado del asistente"}), 500

@asistente_bp.route('/api/historial_conversaciones')
@login_required
def historial_conversaciones():
    try:
        conversaciones = Conversacion.query.filter_by(usuario_id=current_user.id).order_by(Conversacion.fecha.desc()).limit(10).all()
        return jsonify([{
            'id': conv.id,
            'fecha': conv.fecha.isoformat(),
            'contenido': conv.contenido
        } for conv in conversaciones])
    except Exception as e:
        current_app.logger.error(f"Error al obtener el historial de conversaciones: {str(e)}")
        return jsonify({"error": "Error al obtener el historial de conversaciones"}), 500

@asistente_bp.route('/api/borrar_contexto', methods=['POST'])
@login_required
def borrar_contexto():
    try:
        ContextoAsistente.query.filter_by(usuario_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"mensaje": "Contexto del asistente borrado correctamente"})
    except Exception as e:
        current_app.logger.error(f"Error al borrar el contexto del asistente: {str(e)}")
        return jsonify({"error": "Error al borrar el contexto del asistente"}), 500

@asistente_bp.route('/api/obtener_contexto')
@login_required
def obtener_contexto():
    try:
        contexto = ContextoAsistente.query.filter_by(usuario_id=current_user.id).first()
        if contexto:
            return jsonify({
                "contexto": contexto.contexto,
                "fecha_actualizacion": contexto.fecha_actualizacion.isoformat()
            })
        else:
            return jsonify({"mensaje": "No se encontró contexto para este usuario"}), 404
    except Exception as e:
        current_app.logger.error(f"Error al obtener el contexto del asistente: {str(e)}")
        return jsonify({"error": "Error al obtener el contexto del asistente"}), 500