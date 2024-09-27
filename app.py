from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import requests
import json
from admin_routes import admin
from dotenv import load_dotenv
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from admin_routes import admin
import psycopg2
from psycopg2 import pool
import threading
import queue
from flask_migrate import Migrate
from models import db, Usuario, Transaccion, Notificacion, Empresa, Rol, Permiso, Modulo, UsuarioModulo, Cuenta
from mailjet_rest import Client
import secrets
import string
from logging.config import dictConfig
from models import Rol
from banco import banco_bp

load_dotenv()

# Configura logging
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["2000 per day", "500 per hour"])

# Configura tus claves API de Mailjet
mailjet = Client(auth=(os.getenv('MJ_APIKEY_PUBLIC'), os.getenv('MJ_APIKEY_PRIVATE')), version='v3.1')

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

def get_assistant_context():
    with db.app.app_context():
        empresa_count = Empresa.query.count()
        usuario_count = Usuario.query.count()
        return {
            "empresa_count": empresa_count,
            "usuario_count": usuario_count,
        }

class AsistenteVirtual:
    def __init__(self, api_key, db_config, activo=True):
        self.api_key = api_key
        self.context = "Eres un asistente virtual para CalculAI. Debes responder preguntas basándote en la información proporcionada en el contexto y la pregunta del usuario."
        self.db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **db_config)
        self.crear_tablas()
        self.lock = threading.Lock()
        self.cola_actualizaciones = queue.Queue()
        self.activo = activo
        threading.Thread(target=self.procesar_actualizaciones, daemon=True).start()

    def crear_tablas(self):
        with self.db_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS historial (
                        id SERIAL PRIMARY KEY,
                        accion TEXT NOT NULL,
                        fecha TIMESTAMP NOT NULL
                    )
                """)
            conn.commit()
        self.db_pool.putconn(conn)

    def procesar_actualizaciones(self):
        while True:
            try:
                accion = self.cola_actualizaciones.get(timeout=1)
                with self.lock:
                    self.registrar_accion(accion)
            except queue.Empty:
                pass

    def registrar_accion(self, accion):
        fecha = datetime.now()
        with self.db_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO historial (accion, fecha) VALUES (%s, %s)",
                    (accion, fecha)
                )
            conn.commit()
        self.db_pool.putconn(conn)

    def log_accion(self, accion):
        if self.activo:
            self.cola_actualizaciones.put(accion)

    def responder(self, pregunta_con_contexto):
        if not self.activo:
            return "El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación."

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        data = {
            "model": "claude-2.1",
            "prompt": f"{self.context}\n\nHuman: {pregunta_con_contexto}\n\nAssistant:",
            "max_tokens": 300,
            "temperature": 0.7,
            "stop_sequences": ["\n\nHuman:"],
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/complete",
                headers=headers,
                json=data,
                timeout=10,
            )
            response.raise_for_status()
            respuesta = response.json()["completion"].strip()
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                error_detail = e.response.json().get("error", {}).get("message", str(e))
                respuesta = f"Error al obtener respuesta: {error_detail}"
            else:
                respuesta = f"Error de conexión: {str(e)}"
        except Exception as e:
            respuesta = f"Error inesperado: {str(e)}"

        return respuesta

def generate_password():
    """Genera una contraseña aleatoria segura."""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(12))
    return password

from flask import render_template_string
from mailjet_rest import Client
import os

mailjet = Client(auth=(os.environ.get('MJ_APIKEY_PUBLIC'), os.environ.get('MJ_APIKEY_PRIVATE')), version='v3.1')

def send_welcome_email(email, nombre, apellido, login_link, nombre_usuario, password):
    nombre_completo = f"{nombre} {apellido}"
    
    html_content = render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bienvenido a CalculAI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .logo {
                font-size: 2rem;
                font-weight: bold;
                color: #007bff;
            }
            .ai-text {
                color: #2b0ae6;
                font-style: italic;
            }
            h1 {
                color: #007bff;
            }
            .credentials {
                background-color: #e9ecef;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
            }
            .btn {
                display: inline-block;
                background-color: #007bff;
                color: #ffffff;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 5px;
                margin-top: 20px;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                font-size: 0.9rem;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Calcul<span class="ai-text">AI</span></div>
            </div>
            <h1>¡Bienvenido a CalculAI, {{ nombre_completo }}!</h1>
            <p>Estamos emocionados de que comiences tu prueba de 14 días con nosotros.</p>
            <p>Para acceder al sistema, utiliza las siguientes credenciales:</p>
            <div class="credentials">
                <p><strong>Nombre de usuario:</strong> {{ nombre_usuario }}</p>
                <p><strong>Contraseña:</strong> {{ password }}</p>
            </div>
            <p>Durante tu período de prueba, tendrás acceso completo a todas las funcionalidades del sistema.</p>
            <a href="{{ login_link }}" class="btn">Iniciar sesión en CalculAI</a>
            <p>Si tienes alguna duda o necesitas ayuda, no dudes en contactarnos.</p>
            <p>¡Gracias por elegir CalculAI!</p>
            <div class="footer">
                <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """, nombre_completo=nombre_completo, nombre_usuario=nombre_usuario, password=password, login_link=login_link)

    data = {
        'Messages': [
            {
                "From": {
                    "Email": "soporte@sendiu.net",
                    "Name": "CalculAI"
                },
                "To": [
                    {
                        "Email": email,
                        "Name": nombre_completo
                    }
                ],
                "Subject": "Bienvenido a CalculAI - Tu período de prueba de 14 días ha comenzado",
                "HTMLPart": html_content
            }
        ]
    }
    
    try:
        result = mailjet.send.create(data=data)
        return result.status_code, result.json()
    except Exception as e:
        logger.error(f"Error al enviar correo de bienvenida: {str(e)}")
        return 500, {"error": str(e)}

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    if not os.getenv('MJ_APIKEY_PUBLIC') or not os.getenv('MJ_APIKEY_PRIVATE'):
        app.logger.error('Mailjet API keys are not set. Please check your .env file.')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0001@localhost:5432/calculai_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    limiter.init_app(app)

    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(banco_bp, url_prefix='/banco')  # Registra el Blueprint de banco

    with app.app_context():
        db.create_all()

    ASISTENTE_ACTIVO = True
    
    db_config = {
        'dbname': 'calculai_db',
        'user': 'postgres',
        'password': '0001',
        'host': 'localhost',
        'port': '5432'
    }
    asistente = AsistenteVirtual(Config.CLAUDE_API_KEY, db_config, activo=ASISTENTE_ACTIVO)

    setup_logging(app)

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
    @login_required  # Si quieres que solo usuarios registrados vean esta página
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
                    empresa_id=nueva_empresa.id
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
        pregunta = request.json.get('pregunta', '').strip()

        if not pregunta:
            return jsonify({"respuesta": ""}), 200

        if not ASISTENTE_ACTIVO:
            return jsonify({
                "respuesta": "El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación."
            }), 200

        context = get_assistant_context()
        pregunta_con_contexto = f"Contexto: {json.dumps(context)}\n\nPregunta: {pregunta}"
        respuesta = asistente.responder(pregunta_con_contexto)

        logger.info(f"Consulta al asistente: {pregunta}")
        return jsonify({"respuesta": respuesta})

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
            "nombre": "Renyk Morel",
            "id": "P11863",
            "avatar": "/api/placeholder/100/100",
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