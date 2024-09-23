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
from models import db, Usuario, Banco, Transaccion, Notificacion, Empresa, Rol, Permiso, Modulo, UsuarioModulo, Cuenta
from mailjet_rest import Client
import secrets
import string

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
        banco_count = Banco.query.count()
        empresa_count = Empresa.query.count()
        usuario_count = Usuario.query.count()
        return {
            "banco_count": banco_count,
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

def send_welcome_email(user_email, user_name, login_link, username, password):
    """Envía un correo de bienvenida al nuevo usuario."""
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "soporte@sendiu.net",
                    "Name": "CalculAI"
                },
                "To": [
                    {
                        "Email": user_email,
                        "Name": user_name
                    }
                ],
                "Subject": "Bienvenido a CalculAI - Tu período de prueba de 14 días ha comenzado",
                "HTMLPart": f"""
                <h1>Hola {user_name},</h1>
                <p>¡Bienvenido a CalculAI! Estamos emocionados de que comiences tu prueba de 14 días.</p>
                <p>Para acceder al sistema, puedes iniciar sesión usando las siguientes credenciales:</p>
                <ul>
                  <li><strong>Nombre de usuario:</strong> {username}</li>
                  <li><strong>Contraseña:</strong> {password}</li>
                </ul>
                <p>Puedes acceder al sistema a través de este enlace: <a href='{login_link}'>Iniciar sesión en CalculAI</a>.</p>
                <p>Durante tu período de prueba de 14 días, tendrás acceso completo a todas las funcionalidades del sistema.</p>
                <p>Si tienes alguna duda, no dudes en contactarnos.</p>
                <p>¡Gracias por elegir CalculAI!</p>
                """
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
            username = data.get('nombre_usuario')
            email = data.get('email')
            password = generate_password()  # Genera una contraseña aleatoria

            if not all([username, email]):
                return jsonify({"success": False, "error": "Todos los campos son obligatorios"}), 400

            if Usuario.query.filter_by(nombre_usuario=username).first():
                return jsonify({"success": False, "error": "El nombre de usuario ya está en uso"}), 400

            if Usuario.query.filter_by(email=email).first():
                return jsonify({"success": False, "error": "El correo electrónico ya está registrado"}), 400

            try:
                new_user = Usuario(nombre_usuario=username, email=email)
                new_user.set_password(password)  # Asegúrate de que esta línea esté presente
                db.session.add(new_user)
                db.session.commit()

                # Enviar correo de bienvenida
                login_link = url_for('login', _external=True)
                status_code, response = send_welcome_email(email, username, login_link, username, password)

                if status_code == 200:
                    logger.info(f"Nuevo usuario registrado y correo enviado: {username}")
                    return jsonify({"success": True, "message": "Registro exitoso. Por favor, revisa tu correo electrónico para obtener tus credenciales de acceso.", "user_id": new_user.id}), 200
                else:
                    logger.error(f"Error al enviar correo de bienvenida: {response}")
                    return jsonify({"success": True, "message": "Registro exitoso, pero hubo un problema al enviar el correo de bienvenida. Por favor, contacta al soporte.", "user_id": new_user.id}), 200

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error en el registro: {str(e)}")
                return jsonify({"success": False, "error": "Error en el registro"}), 500

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
            "Banco": [
                "Bancos",
                "Depósitos",
                "Notas de Crédito/Débito",
                "Transferencias Bancarias",
                "Conciliación Bancaria",
                "Gestión de Bancos",
                "Divisas",
            ],
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

    @app.route("/bancos")
    @app.route("/Bancos")
    @login_required
    def sub_bancos():
        try:
            bancos = Banco.query.all()
            return render_template("sub_bancos.html", bancos=bancos)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error al cargar la página de bancos: {error_message}")
            return jsonify({"error": f"Error al cargar la página de bancos: {error_message}"}), 500

    @app.route("/Bancos")
    def redirect_to_bancos():
        return redirect(url_for('sub_bancos'))

    @app.route("/api/obtener-banco/<int:id>")
    @login_required
    def obtener_banco(id):
        banco = Banco.query.get_or_404(id)
        return jsonify(banco.to_dict())

    @app.route("/api/actualizar-banco/<int:id>", methods=["PUT"])
    @login_required
    def actualizar_banco(id):
        banco = Banco.query.get_or_404(id)
        datos = request.json
        try:
            for key, value in datos.items():
                if key in ["nombre", "telefono", "contacto", "telefono_contacto", "estatus"]:
                    setattr(banco, key, value)
            db.session.commit()
            logger.info(f"Banco actualizado: {banco.nombre}")
            return jsonify(banco.to_dict())
        except IntegrityError:
            db.session.rollback()
            logger.warning(f"Intento de actualizar banco con nombre o teléfono duplicado: {datos}")
            return jsonify({"error": "Ya existe un banco con ese nombre o teléfono"}), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar banco: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/eliminar-banco/<int:id>", methods=["DELETE"])
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

    @app.route("/api/cambiar-estatus-banco/<int:id>", methods=["PUT"])
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

    @app.route("/api/buscar-bancos")
    @login_required
    def buscar_bancos():
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

    @app.route("/api/crear-banco", methods=["POST"])
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
            return jsonify(nuevo_banco.to_dict()), 201
        except IntegrityError:
            db.session.rollback()
            logger.warning(f"Intento de crear banco con nombre o teléfono duplicado: {datos}")
            return jsonify({"error": "Ya existe un banco con ese nombre o teléfono"}), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear banco: {str(e)}")
            return jsonify({"error": str(e)}), 500

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