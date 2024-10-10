from app import db
from datetime import datetime

class Formulario606(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    rnc_cedula = db.Column(db.String(20), nullable=False)
    tipo_bienes_servicios = db.Column(db.String(100), nullable=False)
    ncf = db.Column(db.String(20), nullable=False)
    monto = db.Column(db.Float, nullable=False)

class Formulario607(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    rnc_cedula = db.Column(db.String(20), nullable=False)
    tipo_ingreso = db.Column(db.String(100), nullable=False)
    ncf = db.Column(db.String(20), nullable=False)
    monto = db.Column(db.Float, nullable=False)

class ReporteIT1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    periodo = db.Column(db.String(7), nullable=False)  # Formato: YYYY-MM
    total_ingresos = db.Column(db.Float, nullable=False)
    total_gastos = db.Column(db.Float, nullable=False)
    impuesto_pagado = db.Column(db.Float, nullable=False)

class ImpuestoRenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ano_fiscal = db.Column(db.Integer, nullable=False)
    ingresos_totales = db.Column(db.Float, nullable=False)
    gastos_deducibles = db.Column(db.Float, nullable=False)
    renta_neta_imponible = db.Column(db.Float, nullable=False)
    impuesto_liquidado = db.Column(db.Float, nullable=False)

class SerieFiscal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serie = db.Column(db.String(20), unique=True, nullable=False)
    tipo_comprobante = db.Column(db.String(50), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    secuencia_desde = db.Column(db.Integer, nullable=False)
    secuencia_hasta = db.Column(db.Integer, nullable=False)
    
class ConfiguracionesImpuestos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tasa_itbis = db.Column(db.Float, default=18.0)
    tasa_isr_personas = db.Column(db.Float, default=25.0)
    tasa_isr_empresas = db.Column(db.Float, default=27.0)
    limite_facturacion_606 = db.Column(db.Float, default=250000.0)    