from extensions import db
from datetime import datetime

class ClienteCxc(db.Model):
    __tablename__ = 'cliente_cxc'
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(20))
    documento = db.Column(db.String(20))
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    provincia = db.Column(db.String(50))
    municipio = db.Column(db.String(50))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    tienda = db.Column(db.String(50))
    tipo_factura = db.Column(db.String(20))
    limite_credito = db.Column(db.Float, default=0)
    dias_gracia = db.Column(db.Integer, default=0)
    retencion_itbis = db.Column(db.Float, default=0)
    retencion_isr = db.Column(db.Float, default=0)
    estado = db.Column(db.String(20), default='activo')
    tipo_cliente_id = db.Column(db.Integer, db.ForeignKey('tipo_cliente.id'))
    
    # Relaciones
    cuentas_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='cliente')
    anticipos = db.relationship('AnticipoCxC', back_populates='cliente')

    def to_dict(self):
        return {
            'id': self.id,
            'tipo_documento': self.tipo_documento,
            'documento': self.documento,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'provincia': self.provincia,
            'municipio': self.municipio,
            'telefono': self.telefono,
            'email': self.email,
            'tienda': self.tienda,
            'tipo_factura': self.tipo_factura,
            'limite_credito': self.limite_credito,
            'dias_gracia': self.dias_gracia,
            'retencion_itbis': self.retencion_itbis,
            'retencion_isr': self.retencion_isr,
            'estado': self.estado,
            'tipo_cliente_id': self.tipo_cliente_id
        }

class TipoCliente(db.Model):
    __tablename__ = 'tipo_cliente'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='activo')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado
        }

class CuentaPorCobrar(db.Model):
    __tablename__ = 'cuenta_por_cobrar'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente_cxc.id'), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True)
    monto = db.Column(db.Float, nullable=False)
    fecha_emision = db.Column(db.Date, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    
    cliente = db.relationship('ClienteCxc', back_populates='cuentas_por_cobrar')
    descuentos_devoluciones = db.relationship('DescuentoDevolucion', back_populates='cuenta_por_cobrar')
    notas_credito = db.relationship('NotaCreditoCxc', back_populates='cuenta_por_cobrar')
    notas_debito = db.relationship('NotaDebitoCxc', back_populates='cuenta_por_cobrar')
    recibos = db.relationship('Recibo', back_populates='cuenta_por_cobrar')

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'numero_documento': self.numero_documento,
            'monto': self.monto,
            'fecha_emision': self.fecha_emision.isoformat(),
            'fecha_vencimiento': self.fecha_vencimiento.isoformat(),
            'estado': self.estado,
            'transacciones': [
                *[dd.to_dict() for dd in self.descuentos_devoluciones],
                *[nc.to_dict() for nc in self.notas_credito],
                *[nd.to_dict() for nd in self.notas_debito],
                *[r.to_dict() for r in self.recibos]
            ]
        }

class DescuentoDevolucion(db.Model):
    __tablename__ = 'descuento_devolucion'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.String(200))
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='descuentos_devoluciones')

    def to_dict(self):
        return {
            'id': self.id,
            'cuenta_por_cobrar_id': self.cuenta_por_cobrar_id,
            'tipo': self.tipo,
            'numero_documento': self.numero_documento,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'descripcion': self.descripcion
        }

class NotaCreditoCxc(db.Model):
    __tablename__ = 'nota_credito_cxc'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='activo')
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='notas_credito')

    def to_dict(self):
        return {
            'id': self.id,
            'cuenta_por_cobrar_id': self.cuenta_por_cobrar_id,
            'numero_documento': self.numero_documento,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo,
            'estado': self.estado
        }

class NotaDebitoCxc(db.Model):
    __tablename__ = 'nota_debito_cxc'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='activo')
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='notas_debito')

    def to_dict(self):
        return {
            'id': self.id,
            'cuenta_por_cobrar_id': self.cuenta_por_cobrar_id,
            'numero_documento': self.numero_documento,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo,
            'estado': self.estado
        }

class Recibo(db.Model):
    __tablename__ = 'recibo'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_por_cobrar_id = db.Column(db.Integer, db.ForeignKey('cuenta_por_cobrar.id'), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    forma_pago = db.Column(db.String(50))
    numero_referencia = db.Column(db.String(50))
    banco = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='activo')
    
    cuenta_por_cobrar = db.relationship('CuentaPorCobrar', back_populates='recibos')

    def to_dict(self):
        return {
            'id': self.id,
            'cuenta_por_cobrar_id': self.cuenta_por_cobrar_id,
            'numero_documento': self.numero_documento,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'forma_pago': self.forma_pago,
            'numero_referencia': self.numero_referencia,
            'banco': self.banco,
            'estado': self.estado
        }

class AnticipoCxC(db.Model):
    __tablename__ = 'anticipo_cxc'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente_cxc.id'), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    forma_pago = db.Column(db.String(50))
    numero_referencia = db.Column(db.String(50))
    banco = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='disponible')
    
    cliente = db.relationship('ClienteCxc', back_populates='anticipos')

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'numero_documento': self.numero_documento,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'forma_pago': self.forma_pago,
            'numero_referencia': self.numero_referencia,
            'banco': self.banco,
            'estado': self.estado
        }

class CondicionPago(db.Model):
    __tablename__ = 'condicion_pago'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    dias = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='activo')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'dias': self.dias,
            'descripcion': self.descripcion,
            'estado': self.estado
        }