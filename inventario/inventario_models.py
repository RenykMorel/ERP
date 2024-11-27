from extensions import db
from sqlalchemy import event, func, text
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

   def __init__(self, **kwargs):
       super(TipoItem, self).__init__(**kwargs)

   @validates('nombre')
   def validate_nombre(self, key, nombre):
       if not nombre:
           raise ValueError("El nombre es requerido")
       return nombre

   @validates('tipo')
   def validate_tipo(self, key, tipo):
       tipos_validos = ['servicio', 'bien', 'cargo']
       if tipo and tipo not in tipos_validos:
           raise ValueError(f"Tipo inválido. Debe ser uno de: {', '.join(tipos_validos)}")
       return tipo

   @validates('estatus')
   def validate_estatus(self, key, estatus):
       estatus_validos = ['activo', 'inactivo']
       if estatus not in estatus_validos:
           raise ValueError(f"Estatus inválido. Debe ser uno de: {', '.join(estatus_validos)}")
       return estatus

   def actualizar_item(self, item):
       """Actualiza un item de inventario basado en la configuración del tipo"""
       if item.tipo == 'producto':
           item.puede_vender = self.es_vendible
           item.usar_itbis = self.usa_itbis
           item.puede_modificar_precio = self.modifica_precio
           item.puede_modificar_impuestos = self.modifica_impuestos
           item.aplica_descuento = self.le_aplica_descuento
           item.permite_precio_negativo = self.precio_negativo
           item.usa_margen = self.usa_margen_ganancia
           
           # Actualizar configuración de compras
           item.puede_comprar = self.es_comprable
           item.proporcional_itbis = self.proporcionalidad_del_itbis
           item.aplica_itbis = self.itbis
           item.aplica_otros_impuestos = self.otros_impuestos
           
           print(f"DEBUG - Actualizando configuración de item {item.nombre}")
           print(f"Vendible: {item.puede_vender}")
           print(f"Usa ITBIS: {item.usar_itbis}")
           print(f"Puede modificar precio: {item.puede_modificar_precio}")

   @classmethod
   def before_update(cls, mapper, connection, target):
       """Evento antes de actualizar un tipo de item"""
       # Actualizar todos los items asociados
       for item in target.items:
           target.actualizar_item(item)

   @classmethod
   def __declare_last__(cls):
       """Registrar eventos de SQLAlchemy"""
       event.listen(cls, 'before_update', cls.before_update)

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
           'updated_at': self.updated_at.isoformat() if self.updated_at else None,
           'items_count': len(self.items) if self.items else 0
       }

   def __repr__(self):
       return f'<TipoItem {self.nombre} ({self.tipo})>'

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
    codigo = db.Column(db.String(50), unique=True)
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

    tipo_item_id = db.Column(db.Integer, db.ForeignKey('tipos_item.id'))

    items_facturas = db.relationship('ItemFactura', back_populates='item')
    items_pre_factura = db.relationship('ItemPreFactura', back_populates='item_inv')
    movimientos = db.relationship('MovimientoInventario', back_populates='item')
    ajustes = db.relationship('AjusteInventario', backref='item')

    def __init__(self, **kwargs):
        super(InventarioItem, self).__init__(**kwargs)
        # El código se asignará después de que se guarde el item
        self.codigo = None

    @classmethod
    def generar_siguiente_codigo(cls):
        """Genera el siguiente código basado en el último ID"""
        ultimo_item = cls.query.order_by(cls.id.desc()).first()
        if ultimo_item:
            return str(ultimo_item.id + 1)
        return "1"

    @validates('codigo')
    def validate_codigo(self, key, codigo):
        # Permitir que el código sea None inicialmente
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
            'codigo': str(self.id) if self.id else None,  # El código será igual al ID
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
            if hasattr(self, key) and key != 'codigo':  # No permitir actualizar el código directamente
                setattr(self, key, value)

    def __repr__(self):
        return f'<InventarioItem {self.id}: {self.nombre}>'

# Evento para asignar el código después de crear el item
@db.event.listens_for(InventarioItem, 'after_insert')
def asignar_codigo(mapper, connection, target):
    """Asigna el código igual al ID después de que se crea el item"""
    if not target.codigo:
        # Usar el ID como código
        connection.execute(
            InventarioItem.__table__.update().
            where(InventarioItem.id == target.id).
            values(codigo=str(target.id))
        )

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