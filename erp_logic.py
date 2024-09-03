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
        except Exception as e:
            return f"Error al obtener respuesta: {str(e)}"

class ERP:
    def __init__(self, claude_api_key):
        self.asistente = AsistenteVirtual(claude_api_key)
        self.modulos = {}
        self.inicializar_modulos()

    def inicializar_modulos(self):
        self.modulos['banco'] = ModuloBanco(self)
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
            "Banco": ["Depósitos", "Notas de Crédito/Débito", "Transferencias Bancarias", "Conciliación Bancaria", "Gestión de bancos"],
            "Contabilidad": ["Cuentas", "Diario", "Mayor General", "Balanza de Comprobación", "Estado de Resultados", "Balance General", "Configuraciones", "Flujo de caja"],
            # Añade los submodulos para los demás módulos aquí...
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

    def obtener_datos(self):
        return {
            "transacciones": self.transacciones,
            "cuentas": self.cuentas,
            "saldo_total": sum(cuenta["saldo"] for cuenta in self.cuentas.values())
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