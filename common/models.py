from extensions import db
from sqlalchemy.orm import validates
from datetime import datetime

class ItemFactura(db.Model):
    __tablename__ = 'items_facturas'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Actualizamos las relaciones
    item = db.relationship('InventarioItem', back_populates='items_facturas')
    factura = db.relationship('Facturacion', back_populates='items')

    @validates('cantidad')
    def validate_cantidad(self, key, value):
        if value <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        return value

    @validates('precio_unitario')
    def validate_precio_unitario(self, key, value):
        if value <= 0:
            raise ValueError("El precio unitario debe ser mayor que cero")
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'factura_id': self.factura_id,
            'item_id': self.item_id,
            'item_codigo': self.item.codigo if self.item else None,
            'item_nombre': self.item.nombre if self.item else None,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.cantidad * self.precio_unitario,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    def __repr__(self):
        return f'<ItemFactura {self.id}>'

class ItemPreFactura(db.Model):
    __tablename__ = 'items_pre_factura'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    pre_factura_id = db.Column(db.Integer, db.ForeignKey('pre_facturas.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Cambiamos las relaciones para usar back_populates
    item_inv = db.relationship('InventarioItem', back_populates='items_pre_factura')  # Cambiamos el nombre de la relación
    pre_factura = db.relationship('PreFactura', back_populates='items')

    @validates('cantidad')
    def validate_cantidad(self, key, value):
        if value <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        return value

    @validates('precio_unitario')
    def validate_precio_unitario(self, key, value):
        if value <= 0:
            raise ValueError("El precio unitario debe ser mayor que cero")
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'pre_factura_id': self.pre_factura_id,
            'item_id': self.item_id,
            'item_codigo': self.item_inv.codigo if self.item_inv else None,  # Actualizamos el nombre
            'item_nombre': self.item_inv.nombre if self.item_inv else None,  # Actualizamos el nombre
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.cantidad * self.precio_unitario,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    def __repr__(self):
        return f'<ItemPreFactura {self.id}>'

class MovimientoInventario(db.Model):
    __tablename__ = 'movimientos_inventarios'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada' o 'salida'
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(100))
    documento_referencia = db.Column(db.String(50))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=True)

    # Relaciones simples sin backref
    item = db.relationship('InventarioItem')
    usuario = db.relationship('Usuario')
    factura = db.relationship('Facturacion')

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        if tipo not in ['entrada', 'salida']:
            raise ValueError("El tipo debe ser 'entrada' o 'salida'")
        return tipo

    @validates('cantidad')
    def validate_cantidad(self, key, cantidad):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        return cantidad

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'motivo': self.motivo,
            'documento_referencia': self.documento_referencia,
            'usuario_id': self.usuario_id,
            'factura_id': self.factura_id
        }

    def __repr__(self):
        return f'<MovimientoInventario {self.tipo}: {self.cantidad}>'