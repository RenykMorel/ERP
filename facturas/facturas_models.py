from extensions import db
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from datetime import datetime
from common.models import ItemFactura, ItemPreFactura, MovimientoInventario

class Facturacion(db.Model):
    __tablename__ = 'facturacion'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estatus = db.Column(db.String(20), default='pendiente')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # Solo mantenemos una relación con ItemFactura
    items = db.relationship('ItemFactura', back_populates='factura', lazy=True)

    cliente = db.relationship('Cliente', backref=db.backref('facturas', lazy=True))
    notas_credito = db.relationship('NotaCredito', backref='factura', lazy=True)
    notas_debito = db.relationship('NotaDebito', backref='factura', lazy=True)

    @validates('numero')
    def validate_unique_numero(self, key, value):
        existing = Facturacion.query.filter(Facturacion.numero == value, Facturacion.id != self.id).first()
        if existing:
            raise IntegrityError("Número de factura ya existe", value, '')
        return value

    @validates('estatus')
    def validate_estatus(self, key, estatus):
        valid_status = ['pendiente', 'pagada', 'anulada']
        if estatus not in valid_status:
            raise ValueError(f"Estatus inválido. Debe ser uno de: {', '.join(valid_status)}")
        return estatus

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente.nombre,
            'fecha': self.fecha.isoformat(),
            'total': self.total,
            'estatus': self.estatus,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<Facturacion {self.numero}>'

class PreFactura(db.Model):
    __tablename__ = 'pre_facturas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estatus = db.Column(db.String(20), default='borrador')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    cliente = db.relationship('Cliente', backref=db.backref('pre_facturas', lazy=True))
    items = db.relationship('ItemPreFactura', back_populates='pre_factura', lazy=True)

    @validates('numero')
    def validate_unique_numero(self, key, value):
        existing = PreFactura.query.filter(PreFactura.numero == value, PreFactura.id != self.id).first()
        if existing:
            raise IntegrityError("Número de pre-factura ya existe", value, '')
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente.nombre,
            'fecha': self.fecha.isoformat(),
            'total': self.total,
            'estatus': self.estatus,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<PreFactura {self.numero}>'

class NotaCredito(db.Model):
    __tablename__ = 'notas_credito'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'factura_id': self.factura_id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo
        }

    def __repr__(self):
        return f'<NotaCredito {self.numero}>'

class NotaDebito(db.Model):
    __tablename__ = 'notas_debito'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'factura_id': self.factura_id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo
        }

    def __repr__(self):
        return f'<NotaDebito {self.numero}>'

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ruc = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'telefono': self.telefono,
            'email': self.email
        }