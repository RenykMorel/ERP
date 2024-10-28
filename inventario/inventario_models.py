from extensions import db
from sqlalchemy.orm import validates
from datetime import datetime
from common.models import ItemFactura, ItemPreFactura, MovimientoInventario

class TipoItem(db.Model):
    __tablename__ = 'tipos_item'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # 'servicio', 'bien', 'cargo'
    estatus = db.Column(db.String(20), default='activo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuración para la venta
    es_vendible = db.Column(db.Boolean, default=True)
    usa_itbis = db.Column(db.Boolean, default=True)
    modifica_precio = db.Column(db.Boolean, default=False)
    modifica_impuestos = db.Column(db.Boolean, default=False)
    le_aplica_descuento = db.Column(db.Boolean, default=True)
    precio_negativo = db.Column(db.Boolean, default=False)
    usa_margen_ganancia = db.Column(db.Boolean, default=True)
    usa_precio_moneda = db.Column(db.Boolean, default=False)
    no_venta_costo_pp = db.Column(db.Boolean, default=False)
    gasto_incurrido_para_el_cliente = db.Column(db.Boolean, default=False)
    
    # Configuración para la compra
    es_comprable = db.Column(db.Boolean, default=True)
    proporcionalidad_del_itbis = db.Column(db.Boolean, default=False)
    itbis = db.Column(db.Boolean, default=True)
    otros_impuestos = db.Column(db.Boolean, default=False)
    no_modifica_precio = db.Column(db.Boolean, default=False)
    modifica_costo = db.Column(db.Boolean, default=True)

    # Relación con InventarioItem
    items = db.relationship('InventarioItem', backref='tipo_item_rel', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'estatus': self.estatus,
            'es_vendible': self.es_vendible,
            'usa_itbis': self.usa_itbis,
            'modifica_precio': self.modifica_precio,
            'modifica_impuestos': self.modifica_impuestos,
            'le_aplica_descuento': self.le_aplica_descuento,
            'precio_negativo': self.precio_negativo,
            'usa_margen_ganancia': self.usa_margen_ganancia,
            'usa_precio_moneda': self.usa_precio_moneda,
            'no_venta_costo_pp': self.no_venta_costo_pp,
            'gasto_incurrido_para_el_cliente': self.gasto_incurrido_para_el_cliente,
            'es_comprable': self.es_comprable,
            'proporcionalidad_del_itbis': self.proporcionalidad_del_itbis,
            'itbis': self.itbis,
            'otros_impuestos': self.otros_impuestos,
            'no_modifica_precio': self.no_modifica_precio,
            'modifica_costo': self.modifica_costo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<TipoItem {self.nombre}>'

class CategoriaItem(db.Model):
    __tablename__ = 'categoria_item'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=True)
    estatus = db.Column(db.String(20), default='activo')
    
    def __init__(self, nombre, descripcion=None, estatus='activo'):
        self.nombre = nombre
        self.descripcion = descripcion
        self.estatus = estatus
    
    def __repr__(self):
        return f'<CategoriaItem {self.nombre}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estatus': self.estatus
        }

class InventarioItem(db.Model):
    __tablename__ = 'items_inventario'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True)  # Permitir NULL
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), nullable=False)
    categoria = db.Column(db.String(50), nullable=True)
    costo = db.Column(db.Float, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    itbis = db.Column(db.Float, nullable=False)
    margen = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    stock_maximo = db.Column(db.Integer, nullable=True)
    unidad_medida = db.Column(db.String(20), nullable=True)
    proveedor = db.Column(db.String(100), nullable=True)
    marca = db.Column(db.String(50), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Nueva relación con TipoItem
    tipo_item_id = db.Column(db.Integer, db.ForeignKey('tipos_item.id'))

    # Mantenemos las relaciones existentes que ya están definidas en common.models
    items_facturas = db.relationship('ItemFactura', back_populates='item')
    items_pre_factura = db.relationship('ItemPreFactura', back_populates='item_inv')
    movimientos = db.relationship('MovimientoInventario', back_populates='item')
    ajustes = db.relationship('AjusteInventario', backref='item')

    @validates('codigo')
    def validate_codigo(self, key, codigo):
        if codigo == '':
            return None
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
    def validate_stock(self, key, value):
        if value is None or value == '':
            return 0 if key != 'stock_maximo' else None
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'tipo_item_id': self.tipo_item_id,
            'tipo_item': self.tipo_item_rel.to_dict() if self.tipo_item_rel else None,
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
    __table_args__ = {'extend_existing': True}
    
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

    def __repr__(self):
        return f'<AjusteInventario de {self.item.nombre}: {self.cantidad_anterior} a {self.cantidad_nueva}>'

def init_db():
    db.create_all()
    
class Almacen(db.Model):
    __tablename__ = 'almacenes'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))
    capacidad = db.Column(db.Float)  # en metros cuadrados
    cuenta_inventario = db.Column(db.String(50))
    es_principal = db.Column(db.Boolean, default=False)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ubicacion': self.ubicacion,
            'capacidad': self.capacidad,
            'cuenta_inventario': self.cuenta_inventario,
            'es_principal': self.es_principal,
            'descripcion': self.descripcion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Almacen {self.nombre}>'   