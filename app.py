from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required,
    UserMixin,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import sqlite3
import threading
import queue
import requests
import json
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://",
)


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Banco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    contacto = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estatus = db.Column(db.Enum("activo", "inactivo"), default="activo")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "contacto": self.contacto,
            "telefono_contacto": self.telefono_contacto,
            "estatus": self.estatus,
        }


class Transaccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255))
    cuenta_id = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "monto": self.monto,
            "descripcion": self.descripcion,
            "cuenta_id": self.cuenta_id,
        }


def get_assistant_context():
    with db.app.app_context():
        banco_count = Banco.query.count()
        return {
            "banco_count": banco_count,
        }


class AsistenteVirtual:
    def __init__(self, api_key, activo=True):
        self.api_key = api_key
        self.context = "Eres un asistente virtual para CalculAI. Debes responder preguntas basándote en la información proporcionada en el contexto y la pregunta del usuario."
        self.conn = sqlite3.connect("asistente_virtual.db", check_same_thread=False)
        self.crear_tablas()
        self.lock = threading.Lock()
        self.cola_actualizaciones = queue.Queue()
        self.activo = activo
        threading.Thread(target=self.procesar_actualizaciones, daemon=True).start()

    def crear_tablas(self):
        with self.conn:
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS historial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accion TEXT NOT NULL,
                    fecha TEXT NOT NULL
                )"""
            )

    def procesar_actualizaciones(self):
        while True:
            try:
                accion = self.cola_actualizaciones.get(timeout=1)
                with self.lock:
                    self.registrar_accion(accion)
            except queue.Empty:
                pass

    def registrar_accion(self, accion):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute(
                "INSERT INTO historial (accion, fecha) VALUES (?, ?)",
                (accion, fecha),
            )

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


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///calculai_db.sqlite"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    limiter.init_app(app)

    app.config["RATELIMIT_STORAGE_URI"] = "memory://"

    with app.app_context():
        db.create_all()

    ASISTENTE_ACTIVO = True
    asistente = AsistenteVirtual(Config.CLAUDE_API_KEY, activo=ASISTENTE_ACTIVO)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = Usuario.query.filter_by(username=username).first()

            if user:
                if check_password_hash(user.password_hash, password):
                    login_user(user)
                    return (
                        jsonify(
                            {"success": True, "message": "Inicio de sesión exitoso"}
                        ),
                        200,
                    )
                else:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "Contraseña incorrecta",
                                "allow_password_reset": True,
                                "username": username,
                            }
                        ),
                        401,
                    )
            else:
                return (
                    jsonify({"success": False, "error": "Usuario no encontrado"}),
                    404,
                )

        return render_template("login.html")

    @app.route("/reset_password", methods=["POST"])
    def reset_password():
        username = request.form.get("username")
        new_password = request.form.get("new_password")
        user = Usuario.query.filter_by(username=username).first()

        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

        if not new_password or len(new_password) < 8:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "La nueva contraseña debe tener al menos 8 caracteres",
                    }
                ),
                400,
            )

        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            return (
                jsonify(
                    {"success": True, "message": "Contraseña actualizada correctamente"}
                ),
                200,
            )
        except Exception as e:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Error al actualizar la contraseña: {str(e)}",
                    }
                ),
                500,
            )

    @app.route("/request_password_reset", methods=["POST"])
    def request_password_reset():
        email = request.form.get("email")
        user = Usuario.query.filter_by(email=email).first()

        if not user:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se encontró un usuario con ese correo electrónico",
                    }
                ),
                404,
            )

        # Aquí normalmente enviarías un correo electrónico con un enlace para restablecer la contraseña
        # Por ahora, simplemente devolveremos un mensaje de éxito
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña",
                }
            ),
            200,
        )

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/registro", methods=["GET", "POST"])
    def registro():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if not all([username, email, password, confirm_password]):
                return (
                    jsonify(
                        {"success": False, "error": "Todos los campos son obligatorios"}
                    ),
                    400,
                )

            if password != confirm_password:
                return (
                    jsonify(
                        {"success": False, "error": "Las contraseñas no coinciden"}
                    ),
                    400,
                )

            if Usuario.query.filter_by(username=username).first():
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "El nombre de usuario ya está en uso",
                        }
                    ),
                    400,
                )

            if Usuario.query.filter_by(email=email).first():
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "El correo electrónico ya está registrado",
                        }
                    ),
                    400,
                )

            try:
                new_user = Usuario(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return jsonify({"success": True, "message": "Registro exitoso"}), 200
            except Exception as e:
                db.session.rollback()
                return (
                    jsonify(
                        {"success": False, "error": f"Error en el registro: {str(e)}"}
                    ),
                    500,
                )

        return render_template("registro.html")

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

    @app.route("/Bancos")
    @login_required
    def sub_bancos():
        try:
            bancos = Banco.query.all()
            return render_template("sub_bancos.html", bancos=bancos)
        except Exception as e:
            error_message = str(e)
            return (
                jsonify(
                    {"error": f"Error al cargar la página de bancos: {error_message}"}
                ),
                500,
            )

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
                if key in [
                    "nombre",
                    "telefono",
                    "contacto",
                    "telefono_contacto",
                    "estatus",
                ]:
                    setattr(banco, key, value)
            db.session.commit()
            return jsonify(banco.to_dict())
        except IntegrityError:
            db.session.rollback()
            return (
                jsonify({"error": "Ya existe un banco con ese nombre o teléfono"}),
                400,
            )
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/eliminar-banco/<int:id>", methods=["DELETE"])
    @login_required
    def eliminar_banco(id):
        banco = Banco.query.get_or_404(id)
        db.session.delete(banco)
        db.session.commit()
        return jsonify({"message": "Banco eliminado correctamente"})

    @app.route("/api/cambiar-estatus-banco/<int:id>", methods=["PUT"])
    @login_required
    def cambiar_estatus_banco(id):
        banco = Banco.query.get_or_404(id)
        datos = request.json
        banco.estatus = datos["estatus"]
        db.session.commit()
        return jsonify(banco.to_dict())

    @app.route("/api/buscar-bancos")
    @login_required
    def buscar_bancos():
        query = Banco.query
        if request.args.get("id"):
            query = query.filter(Banco.id == request.args.get("id"))
        if request.args.get("nombre"):
            query = query.filter(Banco.nombre.ilike(f"%{request.args.get('nombre')}%"))
        if request.args.get("contacto"):
            query = query.filter(
                Banco.contacto.ilike(f"%{request.args.get('contacto')}%")
            )
        if request.args.get("estatus"):
            query = query.filter(Banco.estatus == request.args.get("estatus"))

        bancos = query.all()
        return jsonify([banco.to_dict() for banco in bancos])

    @app.route("/api/crear-banco", methods=["POST"])
    @login_required
    def crear_banco():
        datos = request.json
        try:
            nuevo_banco = Banco(**datos)
            db.session.add(nuevo_banco)
            db.session.commit()
            return jsonify(nuevo_banco.to_dict()), 201
        except IntegrityError:
            db.session.rollback()
            return (
                jsonify({"error": "Ya existe un banco con ese nombre o teléfono"}),
                400,
            )
        except Exception as e:
            db.session.rollback()
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

        transacciones = Transaccion.buscar(
            tipo=tipo, descripcion=descripcion, cuenta_id=cuenta_id
        )
        return jsonify([transaccion.to_dict() for transaccion in transacciones])

    @app.route("/api/crear-transaccion", methods=["POST"])
    @login_required
    def crear_transaccion():
        datos = request.json
        try:
            nueva_transaccion = Transaccion = Transaccion(
                tipo=datos["tipo"],
                monto=datos["monto"],
                descripcion=datos["descripcion"],
                cuenta_id=datos["cuenta_id"],
            )
            db.session.add(nueva_transaccion)
            db.session.commit()
            return jsonify(nueva_transaccion.to_dict()), 201
        except Exception as e:
            db.session.rollback()
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

    @app.route("/api/asistente", methods=["POST"])
    @login_required
    def consultar_asistente():
        pregunta = request.json.get("pregunta", "").strip()

        if not pregunta:
            return jsonify({"respuesta": ""}), 200

        if not ASISTENTE_ACTIVO:
            return (
                jsonify(
                    {
                        "respuesta": "El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación."
                    }
                ),
                200,
            )

        # Obtener el contexto actualizado
        context = get_assistant_context()

        # Añadir el contexto a la pregunta
        pregunta_con_contexto = (
            f"Contexto: {json.dumps(context)}\n\nPregunta: {pregunta}"
        )

        # Procesar la pregunta con el asistente
        respuesta = asistente.responder(pregunta_con_contexto)

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

    return app


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    app = create_app()
    extra_dirs = ["templates/", "static/"]
    extra_files = extra_dirs[:]
    for extra_dir in extra_dirs:
        for dirname, dirs, files in os.walk(extra_dir):
            for filename in files:
                filename = os.path.join(dirname, filename)
                if os.path.isfile(filename):
                    extra_files.append(filename)
    app.run(debug=True, extra_files=extra_files)
