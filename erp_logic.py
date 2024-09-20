import json
import requests
from datetime import datetime

class AsistenteVirtual:
    def __init__(self, api_key):
        self.api_key = api_key
        self.context = "Eres un asistente virtual para CalculAI, un sistema ERP de contabilidad. Debes responder preguntas basándote únicamente en la información proporcionada por el sistema y si quieren hacer cálculos matemáticos ayuda."

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
            return response.json()["completion"].strip()
        except requests.exceptions.RequestException as e:
            return f"Error al obtener respuesta: {str(e)}"

class ERP:
    def __init__(self, claude_api_key):
        self.asistente = AsistenteVirtual(claude_api_key)
        self.modulos = {}
        self.inicializar_modulos()

    def inicializar_modulos(self):
        self.modulos['banco'] = ModuloBanco(self)
        self.modulos['usuario'] = ModuloUsuario(self)
        self.modulos['contabilidad'] = ModuloContabilidad(self)
        # Inicializa otros módulos aquí...

    def obtener_datos_para_analisis(self, tipo_analisis):
        return {
            "ventas": [100, 200, 150],
            "costos": [50, 80, 60],
            "beneficios": [50, 120, 90],
        }

    def obtener_datos_historicos(self):
        return {
            "2021": {"ventas": 1000, "costos": 700},
            "2022": {"ventas": 1200, "costos": 800},
        }

    def get_modulos(self):
        return [
            "Banco", "Contabilidad", "Activos Fijos", "Cuentas Por Cobrar",
            "Cuentas Por Pagar", "Facturacion", "Impuestos", "Inventario",
            "Compras", "Importacion", "Proyectos", "Recursos Humanos"
        ]

    def get_submodulos(self, modulo):
        submodulos = {
            "Banco": ["Bancos", "Depósitos", "Notas de Crédito/Débito", "Transferencias Bancarias", "Conciliación Bancaria", "Gestión de Bancos", "Divisas"],
            "Contabilidad": ["Cuentas", "Diario", "Mayor General", "Balanza de Comprobación", "Estado de Resultados", "Balance General", "Configuraciones", "Flujo de caja"],
            "Activos Fijos": ["Activo Fijo", "Depreciación", "Retiro", "Revalorización", "Tipo de Activo Fijo"],
            "Cuentas Por Cobrar": ["Cliente", "Descuento y devoluciones", "Nota de credito", "Nota de debito", "Recibo", "Anticipo CxC", "Condicion de pago", "Reporte CxC", "Tipo de cliente"],
            "Cuentas Por Pagar": ["Factura Suplidor", "Nota de Crédito", "Nota de Débito", "Orden de Compras", "Suplidor", "Anticipo CxP", "Pago de Contado", "Reporte CxP", "Requisición Cotización", "Solicitud Compras", "Tipo de Suplidor"],
            "Facturacion": ["Facturas", "Pre-facturas", "Notas de Crédito/Débito", "Reporte de Ventas", "Gestión de clientes"],
            "Impuestos": ["Formulario 606", "Formulario 607", "Reporte IT1", "Impuesto sobre la Renta (IR17)", "Serie Fiscal", "Configuraciones"],
            "Inventario": ["Items", "Entrada de Almacén", "Salida de Almacén", "Inventario", "Reporte de Inventario"],
            "Compras": ["Solicitudes de Compra", "Órdenes de Compra", "Recepción de Materiales", "Gastos", "Reporte de Compras/Gastos"],
            "Importacion": ["Expediente de Importacion", "Importador", "Reportes Importacion"],
            "Proyectos": ["Gestión de Proyectos", "Presupuestos", "Facturación por Proyecto"],
            "Recursos Humanos": ["Gestión de Empleados", "Nómina", "Evaluación de Desempeño"],
        }
        return submodulos.get(modulo, [])

    def get_tareas(self):
        return [
            {"descripcion": "Revisar facturas pendientes", "vence": "2023-08-15"},
            {"descripcion": "Preparar informe mensual", "vence": "2023-08-20"},
            {"descripcion": "Reunión con inversores", "vence": "2023-08-25"},
        ]

    def get_notificaciones(self):
        return [
            {"mensaje": "Nuevo cliente registrado", "tipo": "info"},
            {"mensaje": "Factura #1234 vencida", "tipo": "warning"},
            {"mensaje": "Actualización del sistema disponible", "tipo": "info"},
        ]

    def get_datos_graficos(self):
        return {
            "ventas": {
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "values": [100, 200, 150, 300, 250, 400]
            },
            "ingresos_vs_gastos": {
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "ingresos": [1000, 1200, 1100, 1300, 1250, 1400],
                "gastos": [800, 900, 850, 950, 900, 1000]
            },
            "distribucion": {
                "labels": ["Ventas", "Gastos", "Beneficios"],
                "values": [400, 300, 100]
            }
        }

class ModuloBanco:
    def __init__(self, erp_main):
        self.erp_main = erp_main
        self.transacciones = []
        self.cuentas = {
            "1": {"nombre": "Cuenta Corriente", "saldo": 1000},
            "2": {"nombre": "Cuenta de Ahorros", "saldo": 5000}
        }
        self.bancos = []

    def obtener_datos(self):
        return {
            "transacciones": self.transacciones,
            "cuentas": self.cuentas,
            "saldo_total": sum(cuenta["saldo"] for cuenta in self.cuentas.values()),
            "bancos": self.bancos
        }

    def realizar_transaccion(self, tipo, monto, descripcion, cuenta_id):
        if cuenta_id not in self.cuentas:
            return {"error": "Cuenta no encontrada"}
        
        if tipo == "retiro" and monto > self.cuentas[cuenta_id]["saldo"]:
            return {"error": "Saldo insuficiente"}

        transaccion = {
            "fecha": datetime.now().isoformat(),
            "tipo": tipo,
            "monto": monto,
            "descripcion": descripcion,
            "cuenta_id": cuenta_id
        }
        self.transacciones.append(transaccion)

        if tipo == "deposito":
            self.cuentas[cuenta_id]["saldo"] += monto
        elif tipo == "retiro":
            self.cuentas[cuenta_id]["saldo"] -= monto

        return transaccion

    def agregar_banco(self, nombre, contacto, telefono):
        nuevo_banco = {
            "id": len(self.bancos) + 1,
            "nombre": nombre,
            "contacto": contacto,
            "telefono": telefono,
            "estatus": "activo"
        }
        self.bancos.append(nuevo_banco)
        return nuevo_banco

    def obtener_bancos(self):
        return self.bancos

    def actualizar_banco(self, id, datos):
        banco = next((b for b in self.bancos if b["id"] == id), None)
        if banco:
            banco.update(datos)
            return banco
        return None

    def eliminar_banco(self, id):
        banco = next((b for b in self.bancos if b["id"] == id), None)
        if banco:
            self.bancos.remove(banco)
            return True
        return False

class ModuloUsuario:
    def __init__(self, erp_main):
        self.erp_main = erp_main
        self.usuarios = []

    def crear_usuario(self, nombre_usuario, email, password, rol="usuario"):
        nuevo_usuario = {
            "id": len(self.usuarios) + 1,
            "nombre_usuario": nombre_usuario,
            "email": email,
            "password": password,  # En una aplicación real, esto debería estar hasheado
            "rol": rol,
            "estado": "activo"
        }
        self.usuarios.append(nuevo_usuario)
        return nuevo_usuario

    def obtener_usuario(self, id):
        return next((usuario for usuario in self.usuarios if usuario["id"] == id), None)

    def actualizar_usuario(self, id, datos):
        usuario = self.obtener_usuario(id)
        if usuario:
            usuario.update(datos)
            return usuario
        return None

    def eliminar_usuario(self, id):
        usuario = self.obtener_usuario(id)
        if usuario:
            self.usuarios.remove(usuario)
            return True
        return False

    def obtener_todos_usuarios(self):
        return self.usuarios

class ModuloContabilidad:
    def __init__(self, erp_main):
        self.erp_main = erp_main
        self.cuentas = []
        self.asientos = []

    def crear_cuenta(self, codigo, nombre, tipo):
        nueva_cuenta = {
            "id": len(self.cuentas) + 1,
            "codigo": codigo,
            "nombre": nombre,
            "tipo": tipo,
            "saldo": 0
        }
        self.cuentas.append(nueva_cuenta)
        return nueva_cuenta

    def registrar_asiento(self, fecha, descripcion, movimientos):
        nuevo_asiento = {
            "id": len(self.asientos) + 1,
            "fecha": fecha,
            "descripcion": descripcion,
            "movimientos": movimientos
        }
        self.asientos.append(nuevo_asiento)
        self._actualizar_saldos(movimientos)
        return nuevo_asiento

    def _actualizar_saldos(self, movimientos):
        for movimiento in movimientos:
            cuenta = next((c for c in self.cuentas if c["id"] == movimiento["cuenta_id"]), None)
            if cuenta:
                if movimiento["tipo"] == "debe":
                    cuenta["saldo"] += movimiento["monto"]
                elif movimiento["tipo"] == "haber":
                    cuenta["saldo"] -= movimiento["monto"]

    def obtener_balance_general(self):
        activos = sum(c["saldo"] for c in self.cuentas if c["tipo"] == "activo")
        pasivos = sum(c["saldo"] for c in self.cuentas if c["tipo"] == "pasivo")
        patrimonio = activos - pasivos
        return {
            "activos": activos,
            "pasivos": pasivos,
            "patrimonio": patrimonio
        }

    def obtener_estado_resultados(self, fecha_inicio, fecha_fin):
        ingresos = sum(a["monto"] for a in self.asientos if a["fecha"] >= fecha_inicio and a["fecha"] <= fecha_fin and a["tipo"] == "ingreso")
        gastos = sum(a["monto"] for a in self.asientos if a["fecha"] >= fecha_inicio and a["fecha"] <= fecha_fin and a["tipo"] == "gasto")
        utilidad = ingresos - gastos
        return {
            "ingresos": ingresos,
            "gastos": gastos,
            "utilidad": utilidad
        }

# Aquí puedes agregar más módulos según sea necesario