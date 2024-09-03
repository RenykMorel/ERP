from flask import Flask, render_template, jsonify, request
from config import Config
import sqlite3
import threading
import queue
import requests
import json
from datetime import datetime
from modelos import Banco, Transaccion, SessionLocal

app = Flask(__name__)
app.config.from_object(Config)


class AsistenteVirtual:
    def __init__(self, api_key):
        self.api_key = api_key
        self.context = "Eres un asistente virtual para CalculAI. Debes responder preguntas basándote únicamente en la información proporcionada por el sistema y si quieren hacer cálculos matemáticos ayuda."
        self.conn = sqlite3.connect("asistente_virtual.db", check_same_thread=False)
        self.crear_tablas()
        self.lock = threading.Lock()
        self.cola_actualizaciones = queue.Queue()
        threading.Thread(target=self.procesar_actualizaciones, daemon=True).start()

    def crear_tablas(self):
        with self.conn:
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS historial (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    pregunta TEXT NOT NULL,
                                    respuesta TEXT NOT NULL,
                                    fecha TEXT NOT NULL
                                )"""
            )

    def procesar_actualizaciones(self):
        while True:
            # Aquí iría la lógica para procesar las actualizaciones en la cola
            pass

    def responder(self, pregunta):
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

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute(
                "INSERT INTO historial (pregunta, respuesta, fecha) VALUES (?, ?, ?)",
                (pregunta, respuesta, fecha),
            )
        return respuesta


# Crear una instancia del AsistenteVirtual
asistente = AsistenteVirtual(Config.CLAUDE_API_KEY)


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
            "Depósitos",
            "Notas de Crédito/Débito",
            "Transferencias Bancarias",
            "Conciliación Bancaria",
            "Gestión de bancos",
            "Bancos",
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
def bancos():
    bancos = Banco.obtener_todos()
    asistente.responder("El usuario ha accedido a la página de gestión de bancos.")
    return render_template("bancos.html", bancos=bancos)


@app.route("/api/buscar-bancos")
def buscar_bancos():
    id_banco = request.args.get("id")
    nombre = request.args.get("nombre")
    contacto = request.args.get("contacto")
    estatus = request.args.get("estatus")

    bancos = Banco.buscar(
        id=id_banco, nombre=nombre, contacto=contacto, estatus=estatus
    )
    asistente.responder(
        f"Se ha realizado una búsqueda de bancos con los siguientes criterios: ID={id_banco}, Nombre={nombre}, Contacto={contacto}, Estatus={estatus}"
    )
    return jsonify([banco.to_dict() for banco in bancos])


@app.route("/api/crear-banco", methods=["POST"])
def crear_banco():
    datos = request.json
    nuevo_banco = Banco(
        nombre=datos["nombre"],
        telefono=datos["telefono"],
        contacto=datos["contacto"],
        telefono_contacto=datos["telefono_contacto"],
    )
    # Aquí deberías añadir el nuevo banco a la base de datos
    asistente.responder(f"Se ha creado un nuevo banco con el nombre: {datos['nombre']}")
    return jsonify(nuevo_banco.to_dict()), 201


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
    db = SessionLocal()
    try:
        nueva_transaccion = Transaccion(
            tipo=datos["tipo"],
            monto=datos["monto"],
            descripcion=datos["descripcion"],
            cuenta_id=datos["cuenta_id"],
        )
        db.add(nueva_transaccion)
        db.commit()
        db.refresh(nueva_transaccion)
        return jsonify(nueva_transaccion.to_dict()), 201
    finally:
        db.close()


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
    # Esta ruta simula la generación de una imagen de avatar
    # En una implementación real, podrías generar una imagen real aquí
    return f"Placeholder image of {width}x{height}", 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(debug=True)
