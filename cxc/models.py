from extensions import db
from datetime import datetime

class ClienteCxc(db.Model):
    __tablename__ = 'cliente_cxc'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    tipo_cliente_id = db.Column(db.Integer, db.ForeignKey('tipo_cliente.id'))
    
    # Agregando relaciones
    cuentas_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='cliente')
    anticipos = db.relationship('AnticipoCxC', back_populates='cliente')

class TipoCliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)

class CuentaPorCobrar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente_cxc.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha_emision = db.Column(db.Date, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')
    
    cliente = db.relationship('ClienteCxc', back_populates='cuentas_por_cobrar')
    descuentos_devoluciones = db.relationship('DescuentoDevolucion', back_populates='cuenta_por_cobrar')
    notas_credito = db.relationship('NotaCreditoCxc', back_populates='cuenta_por_cobrar')
    notas_debito = db.relationship('NotaDebitoCxc', back_populates='cuenta_por_cobrar')
    recibos = db.relationship('Recibo', back_populates='cuenta_por_cobrar')

class DescuentoDevolucion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'Descuento' o 'Devolución'
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='descuentos_devoluciones')

class NotaCreditoCxc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='notas_credito')

class NotaDebitoCxc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='notas_debito')

class Recibo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='recibos')

class AnticipoCxC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente_cxc.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    
    cliente = db.relationship('ClienteCxc', back_populates='anticipos')

class CondicionPago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    dias = db.Column(db.Integer, nullable=False)