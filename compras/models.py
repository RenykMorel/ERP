from app import db
from datetime import datetime

class SolicitudCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.String(50))
    # Añade más campos según sea necesario

class OrdenCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    proveedor = db.Column(db.String(100))
    total = db.Column(db.Float)
    estado = db.Column(db.String(50))
    # Añade más campos según sea necesario

class RecepcionMateriales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    orden_compra_id = db.Column(db.Integer, db.ForeignKey('orden_compra.id'))
    estado = db.Column(db.String(50))
    # Añade más campos según sea necesario

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(100), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'concepto': self.concepto,
            'monto': self.monto,
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'categoria': self.categoria
        }