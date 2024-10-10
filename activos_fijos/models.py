from app import db
from datetime import datetime

class ActivoFijo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_adquisicion = db.Column(db.Date, nullable=False)
    valor_adquisicion = db.Column(db.Float, nullable=False)
    vida_util = db.Column(db.Integer, nullable=False)  # en años
    valor_residual = db.Column(db.Float)
    estado = db.Column(db.String(20), default='Activo')
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_activo_fijo.id'), nullable=False)

    tipo = db.relationship('TipoActivoFijo', backref=db.backref('activos', lazy=True))

    def __repr__(self):
        return f'<ActivoFijo {self.codigo} - {self.nombre}>'

class TipoActivoFijo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    def __repr__(self):
        return f'<TipoActivoFijo {self.nombre}>'

class Depreciacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activo_fijo.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(50), nullable=False)

    activo = db.relationship('ActivoFijo', backref=db.backref('depreciaciones', lazy=True))

    def __repr__(self):
        return f'<Depreciacion {self.activo.codigo} - {self.fecha}>'

class Retiro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activo_fijo.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(100), nullable=False)
    valor_recuperado = db.Column(db.Float)

    activo = db.relationship('ActivoFijo', backref=db.backref('retiro', uselist=False))

    def __repr__(self):
        return f'<Retiro {self.activo.codigo} - {self.fecha}>'

class Revalorizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activo_id = db.Column(db.Integer, db.ForeignKey('activo_fijo.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    valor_anterior = db.Column(db.Float, nullable=False)
    valor_nuevo = db.Column(db.Float, nullable=False)
    motivo = db.Column(db.String(100), nullable=False)

    activo = db.relationship('ActivoFijo', backref=db.backref('revalorizaciones', lazy=True))

    def __repr__(self):
        return f'<Revalorizacion {self.activo.codigo} - {self.fecha}>'