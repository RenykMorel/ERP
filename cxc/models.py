from extensions import db
from datetime import datetime

class ClienteCxc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    tipo_cliente_id = db.Column(db.Integer, db.ForeignKey('tipo_cliente.id'))

class TipoCliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)

class CuentaPorCobrar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha_emision = db.Column(db.Date, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')

class DescuentoDevolucion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'Descuento' o 'Devolución'
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)

class NotaCreditoCxc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))

class NotaDebitoCxc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))

class Recibo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)

class AnticipoCxC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)

class CondicionPago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    dias = db.Column(db.Integer, nullable=False)