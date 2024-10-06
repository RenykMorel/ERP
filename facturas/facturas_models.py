from extensions import db
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

class Facturacion(db.Model):
    __tablename__ = 'facturacion'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estatus = db.Column(db.String(20), default='pendiente')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    @validates('numero')
    def validate_unique_numero(self, key, value):
        existing = Facturacion.query.filter(Facturacion.numero == value).first()
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
            'cliente': self.cliente,
            'fecha': self.fecha.isoformat(),
            'total': self.total,
            'estatus': self.estatus,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['numero', 'cliente', 'fecha', 'total', 'estatus']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['numero', 'cliente', 'fecha', 'total', 'estatus']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

    def __repr__(self):
        return f'<Facturacion {self.numero}>'

class PreFactura(db.Model):
    __tablename__ = 'pre_facturas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estatus = db.Column(db.String(20), default='borrador')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # Agregar validaciones y métodos similares a la clase Facturacion

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

    # Agregar validaciones y métodos similares a la clase Facturacion

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

    # Agregar validaciones y métodos similares a la clase Facturacion

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

    # Agregar validaciones y métodos similares a la clase Facturacion

# Puedes agregar más modelos según sea necesario para los reportes de ventas y otras funcionalidades