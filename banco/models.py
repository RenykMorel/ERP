from app import db

class Banco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    contacto = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estatus = db.Column(db.String(20), default='activo')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'contacto': self.contacto,
            'telefono_contacto': self.telefono_contacto,
            'estatus': self.estatus
        }