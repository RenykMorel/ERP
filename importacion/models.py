from app import db
from datetime import datetime

class Importador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ruc = db.Column(db.String(20), unique=True, nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Importador {self.nombre}>'

class ExpedienteImportacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_expediente = db.Column(db.String(50), unique=True, nullable=False)
    importador_id = db.Column(db.Integer, db.ForeignKey('importador.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='En Proceso')
    descripcion_mercancia = db.Column(db.Text)
    valor_fob = db.Column(db.Float)
    valor_cif = db.Column(db.Float)
    pais_origen = db.Column(db.String(50))
    fecha_llegada = db.Column(db.Date)
    
    importador = db.relationship('Importador', backref=db.backref('expedientes', lazy=True))

    def __repr__(self):
        return f'<ExpedienteImportacion {self.numero_expediente}>'

class DocumentoImportacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expediente_id = db.Column(db.Integer, db.ForeignKey('expediente_importacion.id'), nullable=False)
    tipo_documento = db.Column(db.String(50), nullable=False)
    numero_documento = db.Column(db.String(50))
    fecha_emision = db.Column(db.Date)
    fecha_vencimiento = db.Column(db.Date)
    archivo_url = db.Column(db.String(200))

    expediente = db.relationship('ExpedienteImportacion', backref=db.backref('documentos', lazy=True))

    def __repr__(self):
        return f'<DocumentoImportacion {self.tipo_documento} - {self.numero_documento}>'

class PagoImportacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expediente_id = db.Column(db.Integer, db.ForeignKey('expediente_importacion.id'), nullable=False)
    tipo_pago = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    comprobante_url = db.Column(db.String(200))

    expediente = db.relationship('ExpedienteImportacion', backref=db.backref('pagos', lazy=True))

    def __repr__(self):
        return f'<PagoImportacion {self.tipo_pago} - {self.monto}>'

class ReporteImportacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_reporte = db.Column(db.String(50), nullable=False)
    archivo_url = db.Column(db.String(200))

    def __repr__(self):
        return f'<ReporteImportacion {self.titulo}>'

    