from extensions import db
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func


class Banco(db.Model):
    __tablename__ = 'bancos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    contacto = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estatus = db.Column(db.String(20), default='activo')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    @validates('nombre', 'telefono')
    def validate_unique_fields(self, key, value):
        if key == 'nombre':
            existing = Banco.query.filter(Banco.nombre == value).first()
        elif key == 'telefono':
            existing = Banco.query.filter(Banco.telefono == value).first()
        if existing:
            raise IntegrityError(f"{key.capitalize()} ya existe", value, '')
        return value

    @validates('estatus')
    def validate_estatus(self, key, estatus):
        valid_status = ['activo', 'inactivo']
        if estatus not in valid_status:
            raise ValueError(f"Estatus inválido. Debe ser uno de: {', '.join(valid_status)}")
        return estatus

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'contacto': self.contacto,
            'telefono_contacto': self.telefono_contacto,
            'estatus': self.estatus,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    @classmethod
    def from_dict(cls, data):
        # Excluimos fecha_creacion y fecha_actualizacion ya que se manejan automáticamente
        allowed_keys = ['nombre', 'telefono', 'contacto', 'telefono_contacto', 'estatus']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        # Excluimos fecha_creacion y fecha_actualizacion ya que se manejan automáticamente
        allowed_keys = ['nombre', 'telefono', 'contacto', 'telefono_contacto', 'estatus']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

    def __repr__(self):
        return f'<Banco {self.nombre}>'

# Add other models here if you have any