from extensions import db
from datetime import datetime

class FacturaSuplidor(db.Model):
    __tablename__ = 'factura_suplidor_cxp'
    id = db.Column(db.Integer, primary_key=True)
    numero_factura = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    suplidor_id = db.Column(db.Integer, db.ForeignKey('suplidor_cxp.id'), nullable=False)
    suplidor = db.relationship('Suplidor', backref=db.backref('facturas', lazy=True))

class NotaCreditoCxp(db.Model):
    __tablename__ = 'nota_credito_cxp'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura_suplidor_cxp.id'), nullable=False)
    factura = db.relationship('FacturaSuplidor', backref=db.backref('notas_credito', lazy=True))

class NotaDebitoCxp(db.Model):
    __tablename__ = 'nota_debito_cxp'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura_suplidor_cxp.id'), nullable=False)
    factura = db.relationship('FacturaSuplidor', backref=db.backref('notas_debito', lazy=True))

class OrdenCompra(db.Model):
    __tablename__ = 'orden_compra_cxp'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    monto_total = db.Column(db.Float, nullable=False)
    suplidor_id = db.Column(db.Integer, db.ForeignKey('suplidor_cxp.id'), nullable=False)
    suplidor = db.relationship('Suplidor', backref=db.backref('ordenes_compra', lazy=True))

class Suplidor(db.Model):
    __tablename__ = 'suplidor_cxp'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ruc = db.Column(db.String(20), unique=True, nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_suplidor_cxp.id'), nullable=False)
    tipo = db.relationship('TipoSuplidor', backref=db.backref('suplidores', lazy=True))

class AnticipoCxP(db.Model):
    __tablename__ = 'anticipo_cxp'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    suplidor_id = db.Column(db.Integer, db.ForeignKey('suplidor_cxp.id'), nullable=False)
    suplidor = db.relationship('Suplidor', backref=db.backref('anticipos', lazy=True))

class PagoContado(db.Model):
    __tablename__ = 'pago_contado_cxp'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura_suplidor_cxp.id'), nullable=False)
    factura = db.relationship('FacturaSuplidor', backref=db.backref('pagos_contado', lazy=True))

class ReporteCxP(db.Model):
    __tablename__ = 'reporte_cxp'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    contenido = db.Column(db.Text)

class RequisicionCotizacion(db.Model):
    __tablename__ = 'requisicion_cotizacion_cxp'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)

class SolicitudCompra(db.Model):
    __tablename__ = 'solicitud_compra_cxp'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)

class TipoSuplidor(db.Model):
    __tablename__ = 'tipo_suplidor_cxp'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)