from extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import func

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    facturas = relationship('Factura', back_populates='cliente')

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

class Factura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = relationship('Cliente', back_populates='facturas')
    estatus = db.Column(db.String(20), nullable=False, default='pendiente')
    items = relationship('ItemFactura', back_populates='factura', cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items)

    def __repr__(self):
        return f'<Factura {self.numero}>'

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'cliente': self.cliente.nombre,
            'estatus': self.estatus,
            'total': self.total,
            'items': [item.to_dict() for item in self.items]
        }

class ItemFactura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura.id'), nullable=False)
    factura = relationship('Factura', back_populates='items')
    descripcion = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __repr__(self):
        return f'<ItemFactura {self.descripcion}>'

    def to_dict(self):
        return {
            'id': self.id,
            'descripcion': self.descripcion,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.subtotal
        }

# Función para generar el próximo número de factura
def generar_numero_factura():
    ultimo_numero = db.session.query(func.max(Factura.numero)).scalar()
    if ultimo_numero:
        # Asumiendo que el número de factura es un string con formato 'F0001'
        ultimo_numero = int(ultimo_numero[1:])
        nuevo_numero = f'F{str(ultimo_numero + 1).zfill(4)}'
    else:
        nuevo_numero = 'F0001'
    return nuevo_numero