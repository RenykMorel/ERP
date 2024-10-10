from app import db
from datetime import datetime

# Clase para cuentas contables (Cuentas.html)
class ContabilidadCuenta(db.Model):
    __tablename__ = 'contabilidad_cuentas'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    saldo = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<ContabilidadCuenta {self.codigo} - {self.nombre}>'

# Clase para el libro diario (diario.html)
class AsientoDiario(db.Model):
    __tablename__ = 'asiento_diario'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('contabilidad_cuentas.id'), nullable=False)
    debe = db.Column(db.Float, default=0.0)
    haber = db.Column(db.Float, default=0.0)

    cuenta = db.relationship('ContabilidadCuenta', backref=db.backref('asientos', lazy=True))

    def __repr__(self):
        return f'<AsientoDiario {self.id} - {self.descripcion}>'

# Clase para el mayor general (mayor_general.html)
class MayorGeneral(db.Model):
    __tablename__ = 'mayor_general'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('contabilidad_cuentas.id'), nullable=False)
    saldo_debe = db.Column(db.Float, default=0.0)
    saldo_haber = db.Column(db.Float, default=0.0)
    saldo_final = db.Column(db.Float, default=0.0)

    cuenta = db.relationship('ContabilidadCuenta', backref=db.backref('mayor', lazy=True))

    def __repr__(self):
        return f'<MayorGeneral {self.cuenta.nombre} - Saldo: {self.saldo_final}>'

# Clase para la balanza de comprobación (balanza_comprobacion.html)
class BalanzaComprobacion(db.Model):
    __tablename__ = 'balanza_comprobacion'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('contabilidad_cuentas.id'), nullable=False)
    debe = db.Column(db.Float, default=0.0)
    haber = db.Column(db.Float, default=0.0)
    saldo_deudor = db.Column(db.Float, default=0.0)
    saldo_acreedor = db.Column(db.Float, default=0.0)

    cuenta = db.relationship('ContabilidadCuenta', backref=db.backref('balanza', lazy=True))

    def __repr__(self):
        return f'<BalanzaComprobacion {self.cuenta.nombre} - Deudor: {self.saldo_deudor} / Acreedor: {self.saldo_acreedor}>'

# Clase para el estado de resultados (estado_resultados.html)
class EstadoResultados(db.Model):
    __tablename__ = 'estado_resultados'
    id = db.Column(db.Integer, primary_key=True)
    ingresos = db.Column(db.Float, default=0.0)
    costos = db.Column(db.Float, default=0.0)
    gastos = db.Column(db.Float, default=0.0)
    utilidad = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<EstadoResultados Utilidad: {self.utilidad}>'

# Clase para el balance general (balance_general.html)
class BalanceGeneral(db.Model):
    __tablename__ = 'balance_general'
    id = db.Column(db.Integer, primary_key=True)
    activos_circulantes = db.Column(db.Float, default=0.0)
    activos_fijos = db.Column(db.Float, default=0.0)
    pasivos_corto_plazo = db.Column(db.Float, default=0.0)
    pasivos_largo_plazo = db.Column(db.Float, default=0.0)
    capital_contable = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<BalanceGeneral Capital: {self.capital_contable}>'

# Clase para configuraciones (configuraciones.html)
class Configuraciones(db.Model):
    __tablename__ = 'configuraciones'
    id = db.Column(db.Integer, primary_key=True)
    parametro = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Configuraciones {self.parametro}: {self.valor}>'

# Clase para flujo de caja (flujo_caja.html)
class FlujoCaja(db.Model):
    __tablename__ = 'flujo_caja'
    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(100), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # Ingreso o Egreso
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<FlujoCaja {self.concepto} - {self.tipo}: {self.monto}>'
