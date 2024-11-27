from extensions import db
from sqlalchemy import event, func
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func, text
from datetime import datetime
from common.models import ItemFactura, ItemPreFactura, MovimientoInventario
from flask import current_app
from flask_login import current_user

class Facturacion(db.Model):
  __tablename__ = 'facturacion'
  __table_args__ = {'extend_existing': True}
  
  id = db.Column(db.Integer, primary_key=True)
  numero = db.Column(db.String(50), unique=True, nullable=False)
  cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
  fecha = db.Column(db.Date, nullable=False)
  total = db.Column(db.Float, nullable=False)
  estatus = db.Column(db.String(20), default='pendiente')
  fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
  fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())
  
  tipo = db.Column(db.String(20), nullable=False, default='contado')
  tipo_pago = db.Column(db.String(20), nullable=False, default='efectivo')
  moneda = db.Column(db.String(10), nullable=False, default='DOP')
  tienda_id = db.Column(db.Integer, db.ForeignKey('tiendafactura.id'), nullable=False)
  vendedor_id = db.Column(db.Integer, db.ForeignKey('vendedores.id'), nullable=False)
  
  descuento_monto = db.Column(db.Float, default=0)
  descuento_porcentaje = db.Column(db.Float, default=0)
  notas = db.Column(db.Text)

  TIPOS_VALIDOS = ['contado', 'credito']
  TIPOS_PAGO_VALIDOS = ['efectivo', 'tarjeta', 'transferencia', 'cheque']
  MONEDAS_VALIDAS = ['DOP', 'USD']
  ESTATUS_VALIDOS = ['pendiente', 'pagada', 'anulada', 'vencida']

  # Relaciones actualizadas 
  items = db.relationship(
      'ItemFactura',
      back_populates='factura',
      lazy=True,
      cascade='all, delete-orphan'
  )
  
  cliente = db.relationship(
      'Cliente',
      backref=db.backref('facturas', lazy=True)
  )
  
  tienda = db.relationship(
      'TiendaFactura',
      foreign_keys=[tienda_id],
      back_populates='facturas', 
      lazy=True
  )
  
  vendedor = db.relationship('Vendedor')
  
  notas_credito = db.relationship(
      'NotaCredito',
      backref='factura',
      lazy=True,
      cascade='all, delete-orphan'
  )
  
  notas_debito = db.relationship(
      'NotaDebito',
      backref='factura',
      lazy=True,
      cascade='all, delete-orphan'
  )

  def __init__(self, **kwargs):
      super(Facturacion, self).__init__(**kwargs)
      self._items_procesados = False

@validates('items')
def validate_items(self, key, item):
    """Validar items y actualizar inventario"""
    try:
        if not item:
            raise ValueError("Item no puede ser nulo")
            
        if not hasattr(item, 'item') or not item.item:
            print(f"DEBUG - Item inválido: {item}")
            raise ValueError(f"Item (ID: {getattr(item, 'item_id', 'N/A')}) no tiene producto asociado")
            
        if not hasattr(item.item, 'tipo'):
            print(f"DEBUG - Tipo no definido para item: {getattr(item.item, 'nombre', 'desconocido')}")
            raise ValueError(f"El producto {getattr(item.item, 'nombre', 'desconocido')} no tiene un tipo definido")

        print(f"DEBUG - Validando item: {item.item.nombre} (Tipo: {item.item.tipo})")
        
        # Procesar producto
        if item.item.tipo == 'producto':
            # Verificar stock
            stock_actual = item.item.stock if item.item.stock is not None else 0
            if stock_actual < item.cantidad:
                # Verificar código de autorización
                override_code = getattr(item, 'override_code', None)
                codigo_activo = CodigoAutorizacion.query.filter_by(
                    tipo='stock_override',
                    activo=True
                ).first()
                
                if override_code and codigo_activo and codigo_activo.codigo == override_code:
                    # Crear item pendiente
                    item_pendiente = ItemPendiente(
                        item_id=item.item.id,
                        cantidad_pendiente=item.cantidad,
                        factura_id=self.id,
                        estado='pendiente',
                        override_code=override_code
                    )
                    db.session.add(item_pendiente)
                    print(f"Item {item.item.nombre} facturado con stock pendiente")
                    return item
                
                raise ValueError(
                    "stock_insuficiente",
                    item.item.id,
                    item.item.nombre,
                    stock_actual,
                    item.cantidad,
                    True,
                    f"Stock insuficiente para {item.item.nombre}. Disponible: {stock_actual}"
                )
            
            try:
                # Crear movimiento de inventario
                movimiento = MovimientoInventario(
                    item_id=item.item.id,
                    tipo='salida',
                    cantidad=item.cantidad,
                    fecha=datetime.utcnow(),
                    usuario_id=self.vendedor_id,
                    comentario=f"Factura {self.numero}"
                )
                db.session.add(movimiento)
                
                # Actualizar stock
                db.session.execute(
                    text('UPDATE items_inventario SET stock = stock - :cantidad WHERE id = :item_id'),
                    {'cantidad': item.cantidad, 'item_id': item.item.id}
                )
                
                # Registrar logs
                print(f"DEBUG - Actualizando stock de {item.item.nombre}")
                print(f"Stock anterior: {stock_actual}")
                print(f"Cantidad vendida: {item.cantidad}")
                
                # Refrescar el objeto producto
                db.session.refresh(item.item)
                print(f"DEBUG - Stock actual en BD: {item.item.stock}")
                
            except Exception as e:
                print(f"ERROR procesando stock: {str(e)}")
                db.session.rollback()
                raise ValueError(f"Error actualizando stock de {item.item.nombre}: {str(e)}")
                
        return item
        
    except Exception as e:
        error_msg = f"Error validando item: {str(e)}"
        print(f"ERROR - {error_msg}")
        raise ValueError(error_msg)

def procesar_items(self):
    """Procesar todos los items de la factura"""
    if not self._items_procesados:
        print(f"DEBUG - Procesando items para factura {self.numero}")
        
        for item in self.items:
            try:
                print(f"DEBUG - Procesando item {getattr(item, 'id', 'Nuevo')}")
                self.validate_items('items', item)
                
            except Exception as e:
                error_msg = f"Error procesando item: {str(e)}"
                print(f"ERROR - {error_msg}")
                db.session.rollback()
                raise ValueError(error_msg)
        
        self._items_procesados = True
        print(f"DEBUG - Items procesados exitosamente para factura {self.numero}")

@classmethod
def before_commit(cls, session):
    """Evento antes del commit"""
    for obj in session.new:
        if isinstance(obj, cls):
            try:
                print(f"Procesando factura antes de commit: {obj.numero}")
                # Procesar cada item
                for item in obj.items:
                    item.procesar_inventario()
            except Exception as e:
                print(f"ERROR en before_commit: {str(e)}")
                raise

@classmethod
def __declare_last__(cls):
    """Registrar eventos de SQLAlchemy"""
    event.listen(db.session, 'before_commit', cls.before_commit)

@validates('numero')
def validate_unique_numero(self, key, value):
    if value is None:
        raise ValueError("El número de factura no puede ser nulo")
    if self.id is None:
        existing = Facturacion.query.filter(
            Facturacion.numero == value
        ).first()
        if existing:
            raise IntegrityError("Número de factura ya existe", value, '')
    return value

@validates('estatus')
def validate_estatus(self, key, estatus):
    if estatus not in self.ESTATUS_VALIDOS:
        raise ValueError(f"Estatus inválido. Debe ser uno de: {', '.join(self.ESTATUS_VALIDOS)}")
    return estatus

@validates('tipo')
def validate_tipo(self, key, tipo):
    if tipo not in self.TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido. Debe ser uno de: {', '.join(self.TIPOS_VALIDOS)}")
    return tipo

@validates('tipo_pago')
def validate_tipo_pago(self, key, tipo_pago):
    if tipo_pago not in self.TIPOS_PAGO_VALIDOS:
        raise ValueError(f"Tipo de pago inválido. Debe ser uno de: {', '.join(self.TIPOS_PAGO_VALIDOS)}")
    return tipo_pago

@validates('moneda')
def validate_moneda(self, key, moneda):
    if moneda not in self.MONEDAS_VALIDAS:
        raise ValueError(f"Moneda inválida. Debe ser una de: {', '.join(self.MONEDAS_VALIDAS)}")
    return moneda

@validates('cliente_id')
def validate_cliente(self, key, cliente_id):
    if getattr(self, 'tipo', None) == 'credito' and not cliente_id:
        raise ValueError("Cliente es obligatorio para facturas a crédito")
    return cliente_id

@validates('tienda_id')
def validate_tienda(self, key, tienda_id):
    if not tienda_id:
        raise ValueError("Debe seleccionar una tienda")
    return tienda_id

@validates('vendedor_id')
def validate_vendedor(self, key, vendedor_id):
    if not vendedor_id:
        raise ValueError("Debe seleccionar un vendedor")
    return vendedor_id

def to_dict(self):
    """Convierte la factura a un diccionario"""
    return {
        'id': self.id,
        'numero': self.numero,
        'cliente_id': self.cliente_id,
        'cliente_nombre': self.cliente.nombre if self.cliente else None,
        'cliente_ruc': self.cliente.ruc if self.cliente else None,
        'fecha': self.fecha.isoformat() if self.fecha else None,
        'total': float(self.total) if self.total else 0,
        'estatus': self.estatus,
        'tipo': self.tipo,
        'tipo_pago': self.tipo_pago,
        'moneda': self.moneda,
        'tienda_id': self.tienda_id,
        'tienda_nombre': self.tienda.nombre if self.tienda else None,
        'vendedor_id': self.vendedor_id,
        'vendedor_nombre': self.vendedor.nombre if self.vendedor else None,
        'descuento_monto': float(self.descuento_monto) if self.descuento_monto else 0,
        'descuento_porcentaje': float(self.descuento_porcentaje) if self.descuento_porcentaje else 0,
        'notas': self.notas,
        'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        'items': [item.to_dict() for item in self.items] if self.items else []
    }

def __repr__(self):
    return f'<Factura {self.numero} ({self.estatus})>'
    
    
# facturas_models.py
# facturas/facturas_models.py

class TiendaFactura(db.Model):
    __tablename__ = 'tiendafactura'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    moneda = db.Column(db.String(3), default='DOP')
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # Relación actualizada para coincidir con Facturacion
    facturas = db.relationship(
        'Facturacion',
        back_populates='tienda',
        lazy=True
    )

    def __repr__(self):
        return f'<TiendaFactura {self.codigo}: {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'moneda': self.moneda,
            'activa': self.activa,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        } 

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
        
class Vendedor(db.Model):
    __tablename__ = 'vendedores'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # Definir la relación aquí con backref
    facturas = db.relationship(
        'Facturacion',
        backref='factura_vendedor',
        lazy=True,
        primaryjoin="Vendedor.id == Facturacion.vendedor_id"
    )

    @validates('codigo')
    def validate_codigo(self, key, codigo):
        if not codigo:
            raise ValueError('El código del vendedor es obligatorio')
        return codigo

    @validates('nombre')
    def validate_nombre(self, key, nombre):
        if not nombre:
            raise ValueError('El nombre del vendedor es obligatorio')
        return nombre

    def __repr__(self):
        return f'<Vendedor {self.codigo}: {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'email': self.email,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }       
        
class ItemPendiente(db.Model):
    __tablename__ = 'items_pendientes'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=True)
    cantidad_pendiente = db.Column(db.Integer, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pendiente')
    override_code = db.Column(db.String(50), nullable=True)

    item = db.relationship('InventarioItem', backref='items_pendientes')
    factura = db.relationship('Facturacion', backref='items_pendientes')     
    
class CodigoAutorizacion(db.Model):
    __tablename__ = 'codigos_autorizacion'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(20), default='stock_override')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, onupdate=datetime.utcnow)
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    activo = db.Column(db.Boolean, default=True)

    creador = db.relationship('Usuario', backref='codigos_autorizacion')

    def __repr__(self):
        return f'<CodigoAutorizacion {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'creado_por': self.creado_por,
            'activo': self.activo
        }