from app import db
from datetime import datetime

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fecha_contratacion = db.Column(db.Date, nullable=False)
    puesto = db.Column(db.String(100), nullable=False)

class Nomina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    salario_bruto = db.Column(db.Float, nullable=False)
    deducciones = db.Column(db.Float, nullable=False)
    salario_neto = db.Column(db.Float, nullable=False)

class EvaluacionDesempeno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha_evaluacion = db.Column(db.Date, nullable=False)
    puntuacion = db.Column(db.Integer, nullable=False)
    comentarios = db.Column(db.Text)