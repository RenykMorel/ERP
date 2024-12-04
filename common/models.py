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
    override_code = db.Column(db.String(50), nullable=True)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    # Relaciones
    item = db.relationship('InventarioItem', back_populates='items_facturas', lazy='joined')
    factura = db.relationship('Facturacion', back_populates='items', lazy='joined')

    def __init__(self, **kwargs):
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
        """Validar cantidad"""
        from facturas.facturas_models import ItemPendiente
        
        if value <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
            
        # Si es un producto y no tiene override_code, validar stock
        if self.item and self.item.tipo == 'producto':
            stock_actual = self.item.stock if self.item.stock is not None else 0
            if stock_actual < value and not getattr(self, 'override_code', None):
                raise ValueError({
                    "error": "stock_insuficiente",
                    "item_id": self.item.id,
                    "nombre": self.item.nombre,
                    "stock_actual": stock_actual,
                    "cantidad_solicitada": value,
                    "mensaje": (
                        f"Stock insuficiente para {self.item.nombre}. "
                        f"Stock actual: {stock_actual}. "
                        "Ingrese código 0001 para autorizar."
                    ),
                    "requiere_autorizacion": True
                })
            
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
        if not self.item or self.item.tipo != 'producto':
            return True
            
        stock_actual = self.item.stock if self.item.stock is not None else 0
        
        # Si hay suficiente stock, proceder normalmente
        if stock_actual >= self.cantidad:
            self.item.stock = stock_actual - self.cantidad
            print(f"Stock actualizado normalmente a: {self.item.stock}")
            return True
            
        # Si no hay suficiente stock
        if not self.override_code:
            raise ValueError({
                "error": "stock_insuficiente",
                "item_id": self.item.id,
                "nombre": self.item.nombre,
                "stock_actual": stock_actual,
                "cantidad_solicitada": self.cantidad,
                "mensaje": (
                    f"Stock insuficiente para {self.item.nombre}. "
                    f"Stock actual: {stock_actual}. "
                    "Se requiere código de autorización para continuar."
                ),
                "requiere_autorizacion": True
            })

        # Verificar código de autorización
        if self.override_code == '0001':
            from facturas.facturas_models import ItemPendiente
            
            # Crear item pendiente por la cantidad total
            item_pendiente = ItemPendiente(
                item_id=self.item.id,
                cantidad_pendiente=self.cantidad,
                factura_id=self.factura.id if self.factura else None,
                estado='pendiente',
                override_code=self.override_code
            )
            db.session.add(item_pendiente)
            print(f"Item pendiente creado: {self.cantidad} unidades")

            # Si hay stock parcial, reducirlo a 0
            if stock_actual > 0:
                self.item.stock = 0
                print("Stock parcial reducido a 0")
            
            return True
        else:
            raise ValueError({
                "error": "codigo_invalido",
                "mensaje": "El código de autorización ingresado no es válido"
            })

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