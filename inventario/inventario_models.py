from extensions import db
from sqlalchemy.orm import validates
from datetime import datetime
from common.models import ItemFactura, ItemPreFactura, MovimientoInventario

class InventarioItem(db.Model):
    __tablename__ = 'items_inventario'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(20), nullable=False)
    categoria = db.Column(db.String(50))
    costo = db.Column(db.Float, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    itbis = db.Column(db.Float, nullable=False)
    margen = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    stock_maximo = db.Column(db.Integer)
    unidad_medida = db.Column(db.String(20))
    proveedor = db.Column(db.String(100))
    marca = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    items_facturas = db.relationship('ItemFactura', back_populates='item')
    items_pre_factura = db.relationship('ItemPreFactura', back_populates='item_inv')
    movimientos = db.relationship('MovimientoInventario', back_populates='item')
    ajustes = db.relationship('AjusteInventario', backref=db.backref('item'))

    @validates('codigo')
    def validate_codigo(self, key, codigo):
        if not codigo:
            raise ValueError('El código no puede estar vacío')
        return codigo

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        if tipo not in ['producto', 'servicio', 'otro']:
            raise ValueError('El tipo debe ser "producto", "servicio" o "otro"')
        return tipo

    @validates('precio', 'costo', 'itbis', 'margen')
    def validate_valores_numericos(self, key, valor):
        if valor < 0:
            raise ValueError(f'El {key} no puede ser negativo')
        return valor

    @validates('stock', 'stock_minimo', 'stock_maximo')
    def validate_stock(self, key, stock):
        if self.tipo == 'servicio' and stock != 0:
            raise ValueError('Los servicios no pueden tener stock')
        if stock < 0:
            raise ValueError(f'El {key} no puede ser negativo')
        return stock

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'costo': self.costo,
            'precio': self.precio,
            'itbis': self.itbis,
            'margen': self.margen,
            'stock': self.stock,
            'stock_minimo': self.stock_minimo,
            'stock_maximo': self.stock_maximo,
            'unidad_medida': self.unidad_medida,
            'proveedor': self.proveedor,
            'marca': self.marca,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    def update_from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        return f'<InventarioItem {self.codigo}: {self.nombre}>'

class AjusteInventario(db.Model):
    __tablename__ = 'ajustes_inventario'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    cantidad_anterior = db.Column(db.Integer, nullable=False)
    cantidad_nueva = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

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
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'usuario_id': self.usuario_id
        }

def init_db():
    db.create_all()