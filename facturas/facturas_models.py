from extensions import db
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from datetime import datetime

class Facturacion(db.Model):
    __tablename__ = 'facturacion'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estatus = db.Column(db.String(20), default='pendiente')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    cliente = db.relationship('Cliente', backref=db.backref('facturas', lazy=True))
    notas_credito = db.relationship('NotaCredito', backref='factura', lazy=True)
    notas_debito = db.relationship('NotaDebito', backref='factura', lazy=True)
    items = db.relationship('ItemFactura', back_populates='factura', lazy=True, cascade='all, delete-orphan')

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

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['numero', 'cliente_id', 'fecha', 'total', 'estatus']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['numero', 'cliente_id', 'fecha', 'total', 'estatus']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

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
    items = db.relationship('ItemPreFactura', back_populates='pre_factura', lazy=True, cascade='all, delete-orphan')

    @validates('numero')
    def validate_unique_numero(self, key, value):
        existing = PreFactura.query.filter(PreFactura.numero == value, PreFactura.id != self.id).first()
        if existing:
            raise IntegrityError("Número de pre-factura ya existe", value, '')
        return value

    @validates('estatus')
    def validate_estatus(self, key, estatus):
        valid_status = ['borrador', 'aprobada', 'rechazada', 'facturada']
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

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['numero', 'cliente_id', 'fecha', 'total', 'estatus']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['numero', 'cliente_id', 'fecha', 'total', 'estatus']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

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

    @validates('numero')
    def validate_unique_numero(self, key, value):
        existing = NotaCredito.query.filter(NotaCredito.numero == value, NotaCredito.id != self.id).first()
        if existing:
            raise IntegrityError("Número de nota de crédito ya existe", value, '')
        return value

    @validates('monto')
    def validate_monto(self, key, monto):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return monto

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'factura_id': self.factura_id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['numero', 'factura_id', 'monto', 'fecha', 'motivo']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['numero', 'factura_id', 'monto', 'fecha', 'motivo']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

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

    @validates('numero')
    def validate_unique_numero(self, key, value):
        existing = NotaDebito.query.filter(NotaDebito.numero == value, NotaDebito.id != self.id).first()
        if existing:
            raise IntegrityError("Número de nota de débito ya existe", value, '')
        return value

    @validates('monto')
    def validate_monto(self, key, monto):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return monto

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'factura_id': self.factura_id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['numero', 'factura_id', 'monto', 'fecha', 'motivo']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['numero', 'factura_id', 'monto', 'fecha', 'motivo']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

    def __repr__(self):
        return f'<NotaDebito {self.numero}>'

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ruc = db.Column(db.String(20), unique=True, nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    @validates('ruc')
    def validate_unique_ruc(self, key, value):
        existing = Cliente.query.filter(Cliente.ruc == value, Cliente.id != self.id).first()
        if existing:
            raise IntegrityError("RUC ya existe", value, '')
        return value

    @validates('email')
    def validate_email(self, key, email):
        if email and '@' not in email:
            raise ValueError("Formato de email inválido")
        return email

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['nombre', 'ruc', 'direccion', 'telefono', 'email']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['nombre', 'ruc', 'direccion', 'telefono', 'email']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

class ItemPreFactura(db.Model):
    __tablename__ = 'items_pre_factura'
    id = db.Column(db.Integer, primary_key=True)
    pre_factura_id = db.Column(db.Integer, db.ForeignKey('pre_facturas.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    item = db.relationship('InventarioItem', back_populates='items_pre_factura')
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
            'item_codigo': self.item.codigo,
            'item_nombre': self.item.nombre,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.cantidad * self.precio_unitario
        }

    def __repr__(self):
        return f'<ItemPreFactura {self.item.codigo} - PreFactura {self.pre_factura_id}>'

class ReporteVentas(db.Model):
    __tablename__ = 'reportes_ventas'
    id = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    total_ventas = db.Column(db.Float, nullable=False)
    numero_facturas = db.Column(db.Integer, nullable=False)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())

    @validates('fecha_inicio', 'fecha_fin')
    def validate_fechas(self, key, fecha):
        if key == 'fecha_fin' and hasattr(self, 'fecha_inicio') and fecha < self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return fecha

    def to_dict(self):
        return {
            'id': self.id,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'total_ventas': self.total_ventas,
            'numero_facturas': self.numero_facturas,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['fecha_inicio', 'fecha_fin', 'total_ventas', 'numero_facturas']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def __repr__(self):
        return f'<ReporteVentas {self.fecha_inicio} - {self.fecha_fin}>'

# Función auxiliar para generar reportes de ventas
def generar_reporte_ventas(fecha_inicio, fecha_fin):
    facturas = Facturacion.query.filter(
        Facturacion.fecha.between(fecha_inicio, fecha_fin),
        Facturacion.estatus == 'pagada'
    ).all()
    
    total_ventas = sum(factura.total for factura in facturas)
    numero_facturas = len(facturas)
    
    reporte = ReporteVentas(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        total_ventas=total_ventas,
        numero_facturas=numero_facturas
    )
    
    db.session.add(reporte)
    db.session.commit()
    
    return reporte

# Importaciones necesarias para las relaciones con modelos en inventario_models.py
from inventario.inventario_models import InventarioItem, ItemFactura

# Definición de ItemFactura si no está en inventario_models.py
if 'ItemFactura' not in globals():
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