from app import db
from datetime import datetime

class Proyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.String(20), default='En progreso')
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    
    presupuestos = db.relationship('Presupuesto', backref='proyecto', lazy=True)
    facturas = db.relationship('FacturacionProyecto', backref='proyecto', lazy=True)

class Presupuesto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='Pendiente')

class FacturacionProyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)
    numero_factura = db.Column(db.String(50), unique=True, nullable=False)
    fecha_emision = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')