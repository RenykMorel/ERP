from openai import OpenAI
from flask import current_app
from extensions import db
import json
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from functools import wraps

# Modelos de base de datos (sin cambios)
class Conversacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    contenido = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Conversacion {self.id}>'

class ContextoAsistente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    contexto = db.Column(db.Text, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ContextoAsistente {self.id}>'

class UsuarioModuloBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulo.id'))
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<UsuarioModuloBot {self.id}>'

class AdminConfiguracionSeguridadBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    politica_contrasenas = db.Column(db.String(200))
    tiempo_sesion = db.Column(db.Integer)  # en minutos
    intentos_login = db.Column(db.Integer)

    def __repr__(self):
        return f'<AdminConfiguracionSeguridadBot {self.id}>'

def db_operation(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error de base de datos en {f.__name__}: {str(e)}")
            db.session.rollback()
            raise
    return decorated_function

class AsistenteVirtual:
    def __init__(self):
        self.client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
        self.context = """Eres un asistente virtual multifuncional para CalculAI. 
        Puedes responder preguntas sobre información financiera y transacciones, 
        así como ayudar con tareas de marketing como generar ideas para campañas 
        y crear contenido para emails. Adapta tu respuesta al tipo de solicitud."""

    @staticmethod
    def object_as_dict(obj):
        return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}

    @db_operation
    def get_db_info(self, usuario_id):
        from models import Usuario, Empresa
        usuario = Usuario.query.options(joinedload(Usuario.empresa)).get(usuario_id)
        if usuario:
            info = {
                'usuario': self.object_as_dict(usuario),
                'empresa': self.object_as_dict(usuario.empresa) if usuario.empresa else None
            }
            return info
        return {}

    @db_operation
    def get_user_modules(self, usuario_id):
        modulos_activos = UsuarioModuloBot.query.filter_by(usuario_id=usuario_id, activo=True).all()
        return [modulo.modulo_id for modulo in modulos_activos]

    @db_operation
    def clean_old_conversations(self, days=30):
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        Conversacion.query.filter(Conversacion.fecha < cutoff_date).delete()
        db.session.commit()

    @db_operation
    def responder(self, pregunta, usuario_id, pagina_actual):
        info_db = self.get_db_info(usuario_id)
        modulos_activos = self.get_user_modules(usuario_id)
        contexto_usuario = ContextoAsistente.query.filter_by(usuario_id=usuario_id).first()
        
        context_updated = self._build_context(info_db, modulos_activos, pagina_actual, contexto_usuario)

        response = self._get_openai_response(context_updated, pregunta)
        respuesta = response.choices[0].message.content

        self._update_context(usuario_id, respuesta, contexto_usuario)
        self._save_conversation(usuario_id, pregunta, respuesta)

        return self.format_response(respuesta)

    def _build_context(self, info_db, modulos_activos, pagina_actual, contexto_usuario):
        context = f"{self.context}\n\n"
        context += f"Información del usuario actual: {json.dumps(info_db)}\n\n"
        context += f"Módulos activos: {json.dumps(modulos_activos)}\n\n"
        context += f"Página actual: {pagina_actual}\n\n"
        
        if contexto_usuario:
            context += f"Contexto previo: {contexto_usuario.contexto}"
        return context

    def _get_openai_response(self, context, pregunta):
        try:
            return self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": pregunta}
                ]
            )
        except Exception as e:
            current_app.logger.error(f"Error al comunicarse con la API de OpenAI: {str(e)}")
            raise

    @db_operation
    def _update_context(self, usuario_id, respuesta, contexto_usuario):
        if contexto_usuario:
            contexto_usuario.contexto = respuesta
            contexto_usuario.fecha_actualizacion = datetime.utcnow()
        else:
            nuevo_contexto = ContextoAsistente(usuario_id=usuario_id, contexto=respuesta)
            db.session.add(nuevo_contexto)

    @db_operation
    def _save_conversation(self, usuario_id, pregunta, respuesta):
        nueva_conversacion = Conversacion(usuario_id=usuario_id, contenido=json.dumps({
            "pregunta": pregunta,
            "respuesta": respuesta
        }))
        db.session.add(nueva_conversacion)

    @staticmethod
    def format_response(respuesta):
        try:
            json_response = json.loads(respuesta)
            if 'tipo' in json_response and 'contenido' in json_response:
                return json_response
        except json.JSONDecodeError:
            pass
        return {"tipo": "texto", "contenido": respuesta}

def create_asistente(app):
    asistente = AsistenteVirtual()
    with app.app_context():
        asistente.clean_old_conversations()
    return asistente