from app import db
from datetime import datetime

class Formulario606(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    rnc_cedula = db.Column(db.String(20), nullable=False)
    tipo_bienes_servicios = db.Column(db.String(100), nullable=False)
    ncf = db.Column(db.String(20), nullable=False)
    monto = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Formulario606 {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'rnc_cedula': self.rnc_cedula,
            'tipo_bienes_servicios': self.tipo_bienes_servicios,
            'ncf': self.ncf,
            'monto': self.monto
        }

class Formulario607(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    rnc_cedula = db.Column(db.String(20), nullable=False)
    tipo_ingreso = db.Column(db.String(100), nullable=False)
    ncf = db.Column(db.String(20), nullable=False)
    monto = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Formulario607 {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'rnc_cedula': self.rnc_cedula,
            'tipo_ingreso': self.tipo_ingreso,
            'ncf': self.ncf,
            'monto': self.monto
        }

class ReporteIT1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    periodo = db.Column(db.String(7), nullable=False)  # Formato: YYYY-MM
    total_ingresos = db.Column(db.Float, nullable=False)
    total_gastos = db.Column(db.Float, nullable=False)
    impuesto_pagado = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<ReporteIT1 {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'periodo': self.periodo,
            'total_ingresos': self.total_ingresos,
            'total_gastos': self.total_gastos,
            'impuesto_pagado': self.impuesto_pagado
        }

class ImpuestoRenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ano_fiscal = db.Column(db.Integer, nullable=False)
    ingresos_totales = db.Column(db.Float, nullable=False)
    gastos_deducibles = db.Column(db.Float, nullable=False)
    renta_neta_imponible = db.Column(db.Float, nullable=False)
    impuesto_liquidado = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<ImpuestoRenta {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'ano_fiscal': self.ano_fiscal,
            'ingresos_totales': self.ingresos_totales,
            'gastos_deducibles': self.gastos_deducibles,
            'renta_neta_imponible': self.renta_neta_imponible,
            'impuesto_liquidado': self.impuesto_liquidado
        }

class SerieFiscal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serie = db.Column(db.String(20), unique=True, nullable=False)
    tipo_comprobante = db.Column(db.String(50), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    secuencia_desde = db.Column(db.Integer, nullable=False)
    secuencia_hasta = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<SerieFiscal {self.serie}>'

    def to_dict(self):
        return {
            'id': self.id,
            'serie': self.serie,
            'tipo_comprobante': self.tipo_comprobante,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat(),
            'secuencia_desde': self.secuencia_desde,
            'secuencia_hasta': self.secuencia_hasta
        }

class ConfiguracionesImpuestos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tasa_itbis = db.Column(db.Float, default=18.0)
    tasa_isr_personas = db.Column(db.Float, default=25.0)
    tasa_isr_empresas = db.Column(db.Float, default=27.0)
    limite_facturacion_606 = db.Column(db.Float, default=250000.0)

    def __repr__(self):
        return f'<ConfiguracionesImpuestos {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tasa_itbis': self.tasa_itbis,
            'tasa_isr_personas': self.tasa_isr_personas,
            'tasa_isr_empresas': self.tasa_isr_empresas,
            'limite_facturacion_606': self.limite_facturacion_606
        }