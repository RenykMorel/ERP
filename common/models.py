from extensions import db
from sqlalchemy import event, func, text
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
   itbis = db.Column(db.Float, default=0)
   comentario = db.Column(db.Text)
   override_code = db.Column(db.String(50), nullable=True)  # Agregar este campo
   fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
   fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    # Relaciones
   item = db.relationship('InventarioItem', back_populates='items_facturas', lazy='joined')
   factura = db.relationship('Facturacion', back_populates='items', lazy='joined')


   def __init__(self, **kwargs):
        # Validar que tenemos los campos requeridos
        if not kwargs.get('item_id'):
            raise ValueError("Se requiere el ID del producto")
        if not kwargs.get('cantidad'):
            raise ValueError("Se requiere la cantidad")
        if 'precio_unitario' not in kwargs:
            raise ValueError("Se requiere el precio unitario")
        
        super(ItemFactura, self).__init__(**kwargs)

   @validates('item_id')
   def validate_item(self, key, item_id):
       from inventario.inventario_models import InventarioItem
       item = InventarioItem.query.get(item_id)
       if not item:
           raise ValueError(f"Producto con ID {item_id} no encontrado")
       return item_id

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

   @validates('itbis')
   def validate_itbis(self, key, value):
       if value < 0 or value > 100:
           raise ValueError("El ITBIS debe estar entre 0 y 100")
       return value

   def calcular_subtotal(self):
       subtotal = self.cantidad * self.precio_unitario
       itbis_monto = subtotal * (self.itbis / 100)
       return subtotal + itbis_monto

   def procesar_inventario(self):
    """Procesa la actualización de inventario para este item"""
    if self.item and self.item.tipo == 'producto':
        try:
            print(f"Procesando inventario para item {self.item.nombre}")
            stock_actual = self.item.stock if self.item.stock is not None else 0
            
            # Si hay código de override, no validar stock
            if not self.override_code:
                if stock_actual < self.cantidad:
                    raise ValueError(f"Stock insuficiente para {self.item.nombre}. Disponible: {stock_actual}")
                
                # Actualizar stock solo si no hay override
                nuevo_stock = stock_actual - self.cantidad
                db.session.execute(
                    text('UPDATE items_inventario SET stock = :nuevo_stock WHERE id = :item_id'),
                    {'nuevo_stock': nuevo_stock, 'item_id': self.item_id}
                )
            
            # Crear movimiento en cualquier caso
            movimiento = MovimientoInventario(
                item_id=self.item_id,
                tipo='salida',
                cantidad=self.cantidad,
                fecha=datetime.utcnow(),
                usuario_id=self.factura.vendedor_id,
                motivo=f"Factura {self.factura.numero}",
                factura_id=self.factura.id
            )
            db.session.add(movimiento)
            
            return True
            
        except Exception as e:
            print(f"Error procesando inventario: {str(e)}")
            db.session.rollback()
            raise

   def to_dict(self):
       return {
           'id': self.id,
           'factura_id': self.factura_id,
           'item_id': self.item_id,
           'item_codigo': self.item.codigo if self.item else None,
           'item_nombre': self.item.nombre if self.item else None,
           'cantidad': self.cantidad,
           'precio_unitario': self.precio_unitario,
           'itbis': self.itbis,
           'comentario': self.comentario,
           'subtotal': self.calcular_subtotal(),
           'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
           'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
       }

   def __repr__(self):
       return f'<ItemFactura {self.id}: {self.item.nombre if self.item else "N/A"} x {self.cantidad}>'

# Las clases ItemPreFactura y MovimientoInventario se mantienen igual

class ItemPreFactura(db.Model):
    __tablename__ = 'items_pre_factura'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    pre_factura_id = db.Column(db.Integer, db.ForeignKey('pre_facturas.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    itbis = db.Column(db.Float, default=0)
    comentario = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    item_inv = db.relationship('InventarioItem', back_populates='items_pre_factura')
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

    @validates('itbis')
    def validate_itbis(self, key, value):
        if value < 0 or value > 100:
            raise ValueError("El ITBIS debe estar entre 0 y 100")
        return value

    def calcular_subtotal(self):
        subtotal = self.cantidad * self.precio_unitario
        itbis_monto = subtotal * (self.itbis / 100)
        return subtotal + itbis_monto

    def to_dict(self):
        return {
            'id': self.id,
            'pre_factura_id': self.pre_factura_id,
            'item_id': self.item_id,
            'item_codigo': self.item_inv.codigo if self.item_inv else None,
            'item_nombre': self.item_inv.nombre if self.item_inv else None,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'itbis': self.itbis,
            'comentario': self.comentario,
            'subtotal': self.calcular_subtotal(),
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
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    motivo = db.Column(db.String(100))
    documento_referencia = db.Column(db.String(50))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=True)

    item = db.relationship('InventarioItem', back_populates='movimientos')
    usuario = db.relationship('Usuario', backref='movimientos_inventario')
    factura = db.relationship('Facturacion', backref='movimientos_inventario')

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
            'factura_id': self.factura_id,
            'item_nombre': self.item.nombre if self.item else None,
            'usuario_nombre': self.usuario.nombre if self.usuario else None
        }

    def __repr__(self):
        return f'<MovimientoInventario {self.tipo}: {self.cantidad}>'

# Eliminamos la clase Tienda ya que ahora usamos TiendaFactura en facturas_models.py