from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, render_template_string, current_app
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import requests
import json
from dotenv import load_dotenv
import sys
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2 import pool
import threading
import queue
from flask_migrate import Migrate
sys.path.append(os.path.join(os.path.dirname(__file__), 'banco'))
from banco_models import Banco
from models import (Usuario, Empresa, Rol, Permiso, Modulo, UsuarioModulo, 
                    Notificacion, Transaccion, Cuenta, AdminPlanSuscripcion, 
                    AdminFactura, AdminConfiguracionSeguridad, AdminReporte)
from mailjet_rest import Client
import secrets
import string
from logging.config import dictConfig
from flask import Blueprint
from extensions import db, login_manager, limiter, migrate
from blinker import signal
from sqlalchemy import event
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import inspect
from sqlalchemy.orm import joinedload
from typing import Any
from typing import Tuple, Dict, Any

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

mailjet = Client(auth=(os.getenv('MJ_APIKEY_PUBLIC'), os.getenv('MJ_APIKEY_PRIVATE')), version='v3.1')

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AsistenteVirtual:
    def __init__(self, api_key, get_context_func):
        self.api_key = api_key
        self.get_context_func = get_context_func
        self.context = "Eres un asistente virtual para CalculAI. Debes responder preguntas basándote en la información proporcionada en el contexto y la pregunta del usuario. Tienes acceso a la información de la base de datos de CalculAI, incluyendo usuarios, empresas, transacciones, cuentas y bancos. Si la pregunta no está relacionada con CalculAI o la información disponible, responde que no puedes ayudar con eso."
        self.base_url = "https://api.anthropic.com/v1/messages"

    def object_as_dict(self, obj):
        def serialize(value):
            if isinstance(value, datetime):
                return value.isoformat()
            return value

        return {c.key: serialize(getattr(obj, c.key))
                for c in inspect(obj).mapper.column_attrs}

    def get_db_info(self):
        info = {}
        
        usuarios = Usuario.query.options(joinedload(Usuario.empresa)).all()
        info['usuarios'] = [self.object_as_dict(u) for u in usuarios]

        empresas = Empresa.query.all()
        info['empresas'] = [self.object_as_dict(e) for e in empresas]

        bancos = Banco.query.all()
        info['bancos'] = [self.object_as_dict(b) for b in bancos]

        return info

    def responder(self, pregunta, usuario_id):
        info_db = self.get_db_info()
        usuario_actual = next((u for u in info_db['usuarios'] if u['id'] == usuario_id), None)
        
        if usuario_actual:
            empresa_actual = next((e for e in info_db['empresas'] if e['id'] == usuario_actual['empresa_id']), None)
            context_updated = f"{self.context}\n\nInformación del usuario actual: {json.dumps(usuario_actual, cls=CustomJSONEncoder)}\n\nInformación de la empresa del usuario: {json.dumps(empresa_actual, cls=CustomJSONEncoder)}\n\nInformación completa del sistema: {json.dumps(info_db, cls=CustomJSONEncoder)}"
        else:
            context_updated = f"{self.context}\n\nInformación completa del sistema: {json.dumps(info_db, cls=CustomJSONEncoder)}"

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        
        data = {
            "model": "claude-2.1",
            "system": context_updated,
            "messages": [
                {"role": "user", "content": pregunta}
            ],
            "max_tokens": 500
        }

        try:
            logger.debug(f"Enviando solicitud a la API de Claude. API Key: {self.api_key[:5]}...")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=15,
            )
            response.raise_for_status()
            logger.info("Respuesta recibida de la API de Claude")
            return response.json()["content"][0]["text"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con la API de Claude: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Respuesta de error: {e.response.text}")
            raise Exception(f"Error al comunicarse con la API de Claude: {str(e)}")

def get_assistant_context():
    with current_app.app_context():
        empresa_count = Empresa.query.count()
        usuario_count = Usuario.query.count()
        return {
            "empresa_count": empresa_count,
            "usuario_count": usuario_count,
        }

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler('calculai.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('CalculAI startup')
    return True

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    if not os.getenv('MJ_APIKEY_PUBLIC') or not os.getenv('MJ_APIKEY_PRIVATE'):
        app.logger.error('Mailjet API keys are not set. Please check your .env file.')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:0001@localhost:5432/calculai_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    limiter.init_app(app)

    from admin_routes import admin
    app.register_blueprint(admin, url_prefix='/admin')
    from banco import banco_bp
    app.register_blueprint(banco_bp, url_prefix='/api')

    with app.app_context():
        from banco_models import Banco
        from models import Usuario, Transaccion, Notificacion, Empresa, Rol, Permiso, Modulo, UsuarioModulo, Cuenta
        db.create_all()
        
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    if not CLAUDE_API_KEY:
        app.logger.error('Claude API key is not set. Please check your .env file.')    

    app.config['ASISTENTE_ACTIVO'] = True
    
    # Asignar el asistente como atributo de la aplicación
    app.asistente: Any = AsistenteVirtual(CLAUDE_API_KEY, get_assistant_context)

    # Configurar el logging
    setup_logging(app)

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
    asistente_notificacion = signal('asistente-notificacion')

    @app.route('/admin/toggle_asistente_usuario/<int:user_id>', methods=['POST'])
    @login_required
    def toggle_asistente_usuario(user_id):
        if current_user.rol != 'admin':
            return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403
        
        usuario = Usuario.query.get_or_404(user_id)
        usuario.asistente_activo = not usuario.asistente_activo
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Asistente {'activado' if usuario.asistente_activo else 'desactivado'} para {usuario.nombre_usuario}",
            "asistente_activo": usuario.asistente_activo
        })

    @asistente_notificacion.connect
    def log_notificacion(sender, mensaje):
        print(f"Notificación al asistente: {mensaje}")
    
    @event.listens_for(Banco, 'after_insert')
    def notificar_nuevo_banco(mapper, connection, target):
        asistente_notificacion.send('Banco', mensaje=f"Nuevo banco creado: {target.nombre}")

    @event.listens_for(Banco, 'after_update')
    def notificar_actualizacion_banco(mapper, connection, target):
        asistente_notificacion.send('Banco', mensaje=f"Banco actualizado: {target.nombre}")    
    
    @app.before_request
    def log_request_info():
        app.logger.debug('Headers: %s', request.headers)
        app.logger.debug('Body: %s', request.get_data())
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("50 por minute")
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            logger.debug(f"Received login attempt - Username: {username}, Password: {'*' * len(password) if password else None}")

            if not username or not password:
                logger.warning("Intento de inicio de sesión con credenciales incompletas")
                return jsonify({
                    "success": False,
                    "error": "Por favor, proporcione un nombre de usuario y contraseña"
                }), 400

            user = Usuario.query.filter_by(nombre_usuario=username).first()

            if user and user.check_password(password):
                login_user(user)
                logger.info(f"Usuario {username} ha iniciado sesión exitosamente")
                return jsonify({
                    "success": True,
                    "message": "Inicio de sesión exitoso"
                }), 200
            else:
                logger.warning(f"Intento de inicio de sesión fallido para el usuario {username}")
                return jsonify({
                    "success": False,
                    "error": "Nombre de usuario o contraseña incorrectos"
                }), 401

        return render_template('login.html')

    @app.route('/registro_exitoso')
    @login_required
    def registro_exitoso():
        return render_template('registro_exitoso.html')

    @app.route('/api/registro_exitoso', methods=['GET'])
    def api_registro_exitoso():
        data = {
            "title": "¡Registro Exitoso!",
            "description": "Tu cuenta ha sido creada correctamente.",
            "message": "Hemos enviado un correo electrónico de confirmación.",
            "emailMessage": "Revisa tu bandeja de entrada o la carpeta de spam para confirmar tu correo.",
            "spamMessage": "Si no recibes el correo, intenta registrarte nuevamente.",
            "loginButtonText": "Iniciar Sesión"
        }
        return jsonify(data)

    @app.route("/Bancos")
    @login_required
    def redirect_to_bancos():
        return redirect(url_for('banco.sub_bancos'))

    @app.route("/reset_password", methods=["POST"])
    def reset_password():
        username = request.form.get("username")
        new_password = request.form.get("new_password")
        user = Usuario.query.filter_by(nombre_usuario=username).first()

        if not user:
            logger.warning(f"Intento de restablecimiento de contraseña para usuario no existente: {username}")
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

        if not new_password or len(new_password) < 8:
            return jsonify({"success": False, "error": "La nueva contraseña debe tener al menos 8 caracteres"}), 400
        try:
            user.set_password(new_password)
            db.session.commit()
            logger.info(f"Contraseña actualizada para el usuario {username}")
            return jsonify({"success": True, "message": "Contraseña actualizada correctamente"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar la contraseña para {username}: {str(e)}")
            return jsonify({"success": False, "error": "Error al actualizar la contraseña"}), 500

    @app.route("/request_password_reset", methods=["POST"])
    def request_password_reset():
        email = request.form.get("email")
        user = Usuario.query.filter_by(email=email).first()

        if not user:
            logger.warning(f"Intento de restablecimiento de contraseña para email no registrado: {email}")
            return jsonify({"success": False, "error": "No se encontró un usuario con ese correo electrónico"}), 404

        logger.info(f"Solicitud de restablecimiento de contraseña para el usuario: {user.nombre_usuario}")
        return jsonify({"success": True, "message": "Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña"}), 200

    @app.route('/logout', methods=['POST'])
    @login_required
    def logout():
        logger.info(f"Usuario {current_user.nombre_usuario} ha cerrado sesión")
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/registro', methods=['GET', 'POST'])
    @limiter.limit("30 per minute")
    def registro():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            data = request.form
            logger.info(f"Datos de registro recibidos: {data}")

            required_fields = ['nombre', 'apellido', 'telefono', 'nombre_usuario', 'email', 
                            'nombre_empresa', 'rnc_empresa', 'direccion_empresa', 'telefono_empresa']
            
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                logger.warning(f"Campos faltantes en el registro: {', '.join(missing_fields)}")
                return jsonify({"success": False, "error": f"Faltan los siguientes campos: {', '.join(missing_fields)}"}), 400

            nombre = data.get('nombre')
            apellido = data.get('apellido')
            telefono = data.get('telefono')
            nombre_usuario = data.get('nombre_usuario')
            email = data.get('email')
            password = generate_password()

            nombre_empresa = data.get('nombre_empresa')
            rnc_empresa = data.get('rnc_empresa')
            direccion_empresa = data.get('direccion_empresa')
            telefono_empresa = data.get('telefono_empresa')

            if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
                return jsonify({"success": False, "error": "El nombre de usuario ya está en uso"}), 400

            if Usuario.query.filter_by(email=email).first():
                return jsonify({"success": False, "error": "El correo electrónico ya está registrado"}), 400

            try:
                nueva_empresa = Empresa(
                    nombre=nombre_empresa,
                    rnc=rnc_empresa,
                    direccion=direccion_empresa,
                    telefono=telefono_empresa,
                    estado="activo"
                )
                db.session.add(nueva_empresa)
                db.session.flush()

                new_user = Usuario(
                    nombre_usuario=nombre_usuario,
                    email=email,
                    nombre=nombre,
                    apellido=apellido,
                    telefono=telefono,
                    empresa_id=nueva_empresa.id,
                    asistente_activo=True
                )
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()

                login_link = url_for('login', _external=True)
                status_code, response = send_welcome_email(email, nombre, apellido, login_link, nombre_usuario, password)

                if status_code == 200:
                    logger.info(f"Nuevo usuario registrado y correo enviado: {nombre_usuario}")
                    return jsonify({
                        "success": True,
                        "message": "Registro exitoso. Por favor, revisa tu correo electrónico para obtener tus credenciales de acceso.",
                        "user_id": new_user.id
                    }), 200
                else:
                    logger.error(f"Error al enviar correo de bienvenida: {response}")
                    return jsonify({
                        "success": True,
                        "message": "Registro exitoso, pero hubo un problema al enviar el correo de bienvenida. Por favor, contacta al soporte.",
                        "user_id": new_user.id
                    }), 200

            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"Error de integridad en el registro: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": "Ya existe un usuario o empresa con esos datos"
                }), 400

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error inesperado en el registro: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": f"Error en el registro: {str(e)}"
                }), 500

        return render_template('registro.html')

    @app.route("/api/modulos")
    @login_required
    def get_modulos():
        modulos = [
            "Banco",
            "Contabilidad",
            "Activos Fijos",
            "Cuentas Por Cobrar",
            "Cuentas Por Pagar",
            "Facturacion",
            "Impuestos",
            "Inventario",
            "Compras",
            "Importacion",
            "Proyectos",
            "Recursos Humanos",
        ]
        return jsonify(modulos)

    @app.route("/api/submodulos/<modulo>")
    @login_required
    def get_submodulos(modulo):
        submodulos = {
            "Contabilidad": [
                "Cuentas",
                "Diario",
                "Mayor General",
                "Balanza de Comprobación",
                "Estado de Resultados",
                "Balance General",
                "Configuraciones",
                "Flujo de caja",
            ],
            "Banco": [
                "Bancos",
                "Depósitos",
                "Notas de Crédito/Débito",
                "Transferencias Bancarias",
                "Conciliación Bancaria",
                "Gestión de Bancos",
                "Divisas",
            ],
            "Activos Fijos": [
                "Activo Fijo",
                "Depreciación",
                "Retiro",
                "Revalorización",
                "Tipo de Activo Fijo",
            ],
            "Cuentas Por Cobrar": [
                "Cliente",
                "Descuento y devoluciones",
                "Nota de credito",
                "Nota de debito",
                "Recibo",
                "Anticipo CxC",
                "Condicion de pago",
                "Reporte CxC",
                "Tipo de cliente",
            ],
            "Cuentas Por Pagar": [
                "Factura Suplidor",
                "Nota de Crédito",
                "Nota de Débito",
                "Orden de Compras",
                "Suplidor",
                "Anticipo CxP",
                "Pago de Contado",
                "Reporte CxP",
                "Requisición Cotización",
                "Solicitud Compras",
                "Tipo de Suplidor",
            ],
            "Facturacion": [
                "Facturas",
                "Pre-facturas",
                "Notas de Crédito/Débito",
                "Reporte de Ventas",
                "Gestión de clientes",
            ],
            "Impuestos": [
                "Formulario 606",
                "Formulario 607",
                "Reporte IT1",
                "Impuesto sobre la Renta (IR17)",
                "Serie Fiscal",
                "Configuraciones",
            ],
            "Inventario": [
                "Items",
                "Entrada de Almacén",
                "Salida de Almacén",
                "Inventario",
                "Reporte de Inventario",
            ],
            "Compras": [
                "Solicitudes de Compra",
                "Órdenes de Compra",
                "Recepción de Materiales",
                "Gastos",
                "Reporte de Compras/Gastos",
            ],
            "Importacion": [
                "Expediente de Importacion",
                "Importador",
                "Reportes Importacion",
            ],
            "Proyectos": [
                "Gestión de Proyectos",
                "Presupuestos",
                "Facturación por Proyecto",
            ],
            "Recursos Humanos": [
                "Gestión de Empleados",
                "Nómina",
                "Evaluación de Desempeño",
            ],
        }
        return jsonify(submodulos.get(modulo, []))

    @app.route("/transacciones")
    @login_required
    def transacciones():
        transacciones = Transaccion.obtener_todos()
        return render_template("transacciones.html", transacciones=transacciones)

    @app.route("/api/buscar-transaccion")
    @login_required
    def buscar_transaccion():
        tipo = request.args.get("tipo")
        descripcion = request.args.get("descripcion")
        cuenta_id = request.args.get("cuenta_id")

        transacciones = Transaccion.buscar(tipo=tipo, descripcion=descripcion, cuenta_id=cuenta_id)
        logger.info(f"Búsqueda de transacciones realizada. Resultados: {len(transacciones)}")
        return jsonify([transaccion.to_dict() for transaccion in transacciones])

    @app.route("/api/crear-transaccion", methods=["POST"])
    @login_required
    def crear_transaccion():
        datos = request.json
        try:
            nueva_transaccion = Transaccion(
                tipo=datos["tipo"],
                monto=datos["monto"],
                descripcion=datos["descripcion"],
                cuenta_id=datos["cuenta_id"],
            )
            db.session.add(nueva_transaccion)
            db.session.commit()
            logger.info(f"Nueva transacción creada: {nueva_transaccion.id}")
            return jsonify(nueva_transaccion.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear transacción: {str(e)}")
            return jsonify({"error": f"Error al crear la transacción: {str(e)}"}), 500

    @app.route("/api/tareas")
    @login_required
    def get_tareas():
        tareas = [
            {"descripcion": "Revisar facturas pendientes", "vence": "2023-08-15"},
            {"descripcion": "Preparar informe mensual", "vence": "2023-08-20"},
            {"descripcion": "Reunión con inversores", "vence": "2023-08-25"},
        ]
        return jsonify(tareas)

    @app.route("/api/notificaciones")
    @login_required
    def get_notificaciones():
        notificaciones = [
            {"mensaje": "Nuevo cliente registrado", "tipo": "info"},
            {"mensaje": "Factura #1234 vencida", "tipo": "warning"},
            {"mensaje": "Actualización del sistema disponible", "tipo": "info"},
        ]
        return jsonify(notificaciones)

    @app.route('/api/asistente', methods=['POST'])
    @login_required
    def consultar_asistente():
        logger.debug(f"Solicitud al asistente recibida. Usuario: {current_user.nombre_usuario}")
        if not app.config['ASISTENTE_ACTIVO'] or not current_user.asistente_activo:
            logger.warning(f"Intento de uso del asistente por usuario no autorizado: {current_user.nombre_usuario}")
            return jsonify({"respuesta": "El asistente no está activo para tu usuario. Contacta al administrador."}), 403

        pregunta = request.json.get('pregunta', '').strip()
        logger.debug(f"Pregunta recibida: {pregunta}")
        if not pregunta:
            return jsonify({"respuesta": "Por favor, proporciona una pregunta."}), 400
        
        try:
            respuesta = app.asistente.responder(pregunta, current_user.id)
            logger.info(f"Respuesta del asistente obtenida. Longitud: {len(respuesta)}")
            return jsonify({"respuesta": respuesta})
        except Exception as e:
            logger.error(f"Error al consultar el asistente: {str(e)}")
            return jsonify({"respuesta": "Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde."}), 500


    @app.route('/api/asistente_status')
    @login_required
    def asistente_status():
        return jsonify({
            "activo": current_user.asistente_activo and app.config['ASISTENTE_ACTIVO']
        })

    @app.route('/api/actualizar_estado_asistente', methods=['POST'])
    @login_required
    def actualizar_estado_asistente():
        if current_user.rol != 'admin':
            return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403
        
        nuevo_estado = request.json.get('activo', False)
        app.config['ASISTENTE_ACTIVO'] = nuevo_estado
        return jsonify({"mensaje": "Estado del asistente actualizado correctamente"})

    @app.route("/api/datos_graficos")
    @login_required
    def get_datos_graficos():
        datos = {
            "ventas": {
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "values": [100, 200, 150, 300, 250, 400],
            },
            "ingresos_vs_gastos": {
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "ingresos": [1000, 1200, 1100, 1300, 1250, 1400],
                "gastos": [800, 900, 850, 950, 900, 1000],
            },
            "distribucion": {
                "labels": ["Ventas", "Gastos", "Beneficios"],
                "values": [400, 300, 100],
            },
        }
        return jsonify(datos)

    @app.route("/api/usuario")
    @login_required
    def get_usuario():
        usuario = {
            "nombre": f"{current_user.nombre} {current_user.apellido}",
            "id": current_user.id,
            "avatar": "/api/placeholder/100/100",
            "empresa": current_user.empresa.nombre if current_user.empresa else "Sin empresa"
        }
        return jsonify(usuario)

    @app.route("/api/placeholder/<int:width>/<int:height>")
    def placeholder_image(width, height):
        return (
            f"Placeholder image of {width}x{height}",
            200,
            {"Content-Type": "text/plain"},
        )

    @app.route("/admin_panel")
    @login_required
    def admin_panel():
        if current_user.rol != "admin":
            flash("Acceso no autorizado", "error")
            return redirect(url_for("index"))
        return render_template("admin_panel.html")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)