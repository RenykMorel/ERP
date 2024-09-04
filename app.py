from flask import Flask, render_template, jsonify, request
from config import Config
import sqlite3
import threading
import queue
import requests
import json
import os
import sys
from datetime import datetime
from modelos import db, Banco, Transaccion, init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        init_db(app)

    # Configuración para el asistente
    ASISTENTE_ACTIVO = False  # Cambie a True para activar el asistente

    class AsistenteVirtual:
        def __init__(self, api_key, activo=False):
            self.api_key = api_key
            self.context = "Eres un asistente virtual para CalculAI. Debes responder preguntas basándote únicamente en la información proporcionada por el sistema, no respondas ni digas nada hasta que te hagan la pregunta"
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

        def responder(self, pregunta):
            if not self.activo:
                return "El asistente virtual está desactivado en este momento."

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            data = {
                "model": "claude-2.1",
                "prompt": f"{self.context}\n\nHuman: {pregunta}\n\nAssistant:",
                "max_tokens_to_sample": 300,
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
            except Exception as e:
                respuesta = f"Error al obtener respuesta: {str(e)}"

            return respuesta

    # Crear una instancia del AsistenteVirtual
    asistente = AsistenteVirtual(Config.CLAUDE_API_KEY, activo=ASISTENTE_ACTIVO)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/modulos")
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
    def get_submodulos(modulo):
        submodulos = {
            "Banco": [
                "Bancos",
                "Depósitos",
                "Notas de Crédito/Débito",
                "Transferencias Bancarias",
                "Conciliación Bancaria",
                "Gestión de bancos",
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
    def sub_bancos():
        try:
            bancos = Banco.obtener_todos()
            return render_template("sub_bancos.html", bancos=bancos)
        except Exception as e:
            error_message = str(e)
            return (
                jsonify(
                    {"error": f"Error al cargar la página de bancos: {error_message}"}
                ),
                500,
            )

    @app.route("/api/buscar-bancos")
    def buscar_bancos():
        id_banco = request.args.get("id")
        nombre = request.args.get("nombre")
        contacto = request.args.get("contacto")
        estatus = request.args.get("estatus")

        bancos = Banco.buscar(
            id=id_banco, nombre=nombre, contacto=contacto, estatus=estatus
        )
        return jsonify([banco.to_dict() for banco in bancos])

    @app.route("/api/crear-banco", methods=["POST"])
    def crear_banco():
        datos = request.json
        try:
            nuevo_banco = Banco(
                nombre=datos["nombre"],
                telefono=datos["telefono"],
                contacto=datos["contacto"],
                telefono_contacto=datos["telefono_contacto"],
            )
            db.session.add(nuevo_banco)
            db.session.commit()
            return jsonify(nuevo_banco.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error al crear el banco: {str(e)}"}), 500

    @app.route("/transacciones")
    def transacciones():
        transacciones = Transaccion.obtener_todos()
        return render_template("transacciones.html", transacciones=transacciones)

    @app.route("/api/buscar-transaccion")
    def buscar_transaccion():
        tipo = request.args.get("tipo")
        descripcion = request.args.get("descripcion")
        cuenta_id = request.args.get("cuenta_id")

        transacciones = Transaccion.buscar(
            tipo=tipo, descripcion=descripcion, cuenta_id=cuenta_id
        )
        return jsonify([transaccion.to_dict() for transaccion in transacciones])

    @app.route("/api/crear-transaccion", methods=["POST"])
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
            return jsonify(nueva_transaccion.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error al crear la transacción: {str(e)}"}), 500

    @app.route("/api/tareas")
    def get_tareas():
        tareas = [
            {"descripcion": "Revisar facturas pendientes", "vence": "2023-08-15"},
            {"descripcion": "Preparar informe mensual", "vence": "2023-08-20"},
            {"descripcion": "Reunión con inversores", "vence": "2023-08-25"},
        ]
        return jsonify(tareas)

    @app.route("/api/notificaciones")
    def get_notificaciones():
        notificaciones = [
            {"mensaje": "Nuevo cliente registrado", "tipo": "info"},
            {"mensaje": "Factura #1234 vencida", "tipo": "warning"},
            {"mensaje": "Actualización del sistema disponible", "tipo": "info"},
        ]
        return jsonify(notificaciones)

    @app.route("/api/asistente", methods=["POST"])
    def consultar_asistente():
        if not ASISTENTE_ACTIVO:
            return (
                jsonify(
                    {
                        "respuesta": "El asistente virtual está desactivado en este momento."
                    }
                ),
                200,
            )

        pregunta = request.json.get("pregunta")
        if not pregunta:
            return jsonify({"error": "No se proporcionó una pregunta"}), 400
        respuesta = asistente.responder(pregunta)
        return jsonify({"respuesta": respuesta})

    @app.route("/api/datos_graficos")
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
