from extensions import db
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from datetime import datetime

class InventarioItem(db.Model):
    __tablename__ = 'items_inventario'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(20), nullable=False)  # 'producto' o 'servicio'
    categoria = db.Column(db.String(50))
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    movimientos = db.relationship('MovimientoInventario', back_populates='item', cascade='all, delete-orphan')
    ajustes = db.relationship('AjusteInventario', back_populates='item', cascade='all, delete-orphan')
    items_factura = db.relationship('ItemFactura', back_populates='item', cascade='all, delete-orphan')
    items_pre_factura = db.relationship('ItemPreFactura', back_populates='item', cascade='all, delete-orphan')

    @validates('codigo')
    def validate_codigo(self, key, codigo):
        if not codigo:
            raise ValueError('El código no puede estar vacío')
        existing_item = InventarioItem.query.filter(InventarioItem.codigo == codigo, InventarioItem.id != self.id).first()
        if existing_item:
            raise IntegrityError('Este código ya está en uso', codigo, 'codigo')
        return codigo

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        if tipo not in ['producto', 'servicio']:
            raise ValueError('El tipo debe ser "producto" o "servicio"')
        return tipo

    @validates('precio')
    def validate_precio(self, key, precio):
        if precio < 0:
            raise ValueError('El precio no puede ser negativo')
        return precio

    @validates('stock')
    def validate_stock(self, key, stock):
        if self.tipo == 'servicio' and stock != 0:
            raise ValueError('Los servicios no pueden tener stock')
        if stock < 0:
            raise ValueError('El stock no puede ser negativo')
        return stock

    def __repr__(self):
        return f'<InventarioItem {self.codigo}: {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'precio': self.precio,
            'stock': self.stock,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

    def update_from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class MovimientoInventario(db.Model):
    __tablename__ = 'movimientos_inventario'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada' o 'salida'
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(100))
    documento_referencia = db.Column(db.String(50))  # Por ejemplo, número de factura o nota de entrada
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    item = db.relationship('InventarioItem', back_populates='movimientos')
    usuario = db.relationship('Usuario', backref='movimientos_inventario')

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        if tipo not in ['entrada', 'salida']:
            raise ValueError('El tipo debe ser "entrada" o "salida"')
        return tipo

    @validates('cantidad')
    def validate_cantidad(self, key, cantidad):
        if cantidad <= 0:
            raise ValueError('La cantidad debe ser mayor que cero')
        return cantidad

    def __repr__(self):
        return f'<MovimientoInventario {self.tipo}: {self.cantidad} de {self.item.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'tipo': self.tipo,
            'cantidad': self.cantidad,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo,
            'documento_referencia': self.documento_referencia,
            'usuario_id': self.usuario_id
        }

class AjusteInventario(db.Model):
    __tablename__ = 'ajustes_inventario'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    cantidad_anterior = db.Column(db.Integer, nullable=False)
    cantidad_nueva = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    item = db.relationship('InventarioItem', back_populates='ajustes')
    usuario = db.relationship('Usuario', backref='ajustes_inventario')

    @validates('cantidad_nueva')
    def validate_cantidad_nueva(self, key, cantidad):
        if cantidad < 0:
            raise ValueError('La cantidad nueva no puede ser negativa')
        return cantidad

    def __repr__(self):
        return f'<AjusteInventario de {self.item.nombre}: {self.cantidad_anterior} a {self.cantidad_nueva}>'

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'cantidad_anterior': self.cantidad_anterior,
            'cantidad_nueva': self.cantidad_nueva,
            'motivo': self.motivo,
            'fecha': self.fecha.isoformat(),
            'usuario_id': self.usuario_id
        }

class ItemFactura(db.Model):
    __tablename__ = 'items_factura'
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    item = db.relationship('InventarioItem', back_populates='items_factura')
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
            'item_codigo': self.item.codigo,
            'item_nombre': self.item.nombre,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.cantidad * self.precio_unitario
        }

    def __repr__(self):
        return f'<ItemFactura {self.item.codigo} - Factura {self.factura_id}>'

def init_db():
    db.create_all()

# Importaciones necesarias para las relaciones con modelos en facturas_models.py
from facturas.facturas_models import Facturacion, ItemPreFactura