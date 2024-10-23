from app import db
from datetime import datetime
from sqlalchemy.orm import validates
from sqlalchemy import event

# Excepciones personalizadas
class CuentaContableError(Exception):
    """Excepción base para errores de cuentas contables"""
    pass

class DuplicadaError(CuentaContableError):
    """Se levanta cuando se intenta crear una cuenta duplicada"""
    pass

class FormatoInvalidoError(CuentaContableError):
    """Se levanta cuando el formato de los datos es inválido"""
    pass

# Modelos principales
class ContabilidadCuenta(db.Model):
    __tablename__ = 'contabilidad_cuentas'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(20), nullable=False)
    numero_cuenta = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    origen = db.Column(db.String(20))  # DEBITO/CREDITO
    categoria = db.Column(db.String(20))  # CONTROL/AUXILIAR
    nivel = db.Column(db.Integer)
    padre_id = db.Column(db.String(20))
    tipo = db.Column(db.String(50))      # Detalle/Grupo
    grupo = db.Column(db.String(50))      # Activo/Pasivo/Patrimonio/Ingreso/Gasto
    descripcion = db.Column(db.Text)
    estatus = db.Column(db.String(20), default='Activo')
    saldo = db.Column(db.Numeric(precision=15, scale=2), default=0)
    flujo_efectivo = db.Column(db.String(20))
    corriente = db.Column(db.Boolean, default=False)
    balance_general = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asientos = db.relationship('AsientoDiario', back_populates='cuenta', lazy='dynamic')
    mayor = db.relationship('MayorGeneral', back_populates='cuenta', lazy='dynamic')
    balanza = db.relationship('BalanzaComprobacion', back_populates='cuenta', lazy='dynamic')

    @validates('numero_cuenta')
    def validate_numero_cuenta(self, key, numero_cuenta):
        """Valida y establece el número de cuenta"""
        if not numero_cuenta:
            raise FormatoInvalidoError("El número de cuenta es requerido")
        self.codigo = numero_cuenta  # Auto-asignar código
        self.calcular_nivel_y_padre()
        return numero_cuenta

    @validates('origen')
    def validate_origen(self, key, origen):
        """Valida el origen de la cuenta"""
        if origen and origen.upper() not in ['DEBITO', 'CREDITO']:
            raise FormatoInvalidoError("El origen debe ser DEBITO o CREDITO")
        return origen.upper() if origen else None

    @validates('categoria')
    def validate_categoria(self, key, categoria):
        """Valida la categoría de la cuenta"""
        if categoria and categoria.upper() not in ['CONTROL', 'AUXILIAR']:
            raise FormatoInvalidoError("La categoría debe ser CONTROL o AUXILIAR")
        return categoria.upper() if categoria else None

    def calcular_nivel_y_padre(self):
        """Calcula el nivel y encuentra el padre basado en el número de cuenta"""
        if not hasattr(self, 'numero_cuenta') or not self.numero_cuenta:
            return
            
        self.nivel = len(str(self.numero_cuenta).replace('.', ''))
        numero = str(self.numero_cuenta)
        
        if len(numero) > 1:
            posible_padre = numero[:-1]
            while len(posible_padre) > 0:
                padre = ContabilidadCuenta.query.filter_by(
                    numero_cuenta=posible_padre
                ).first()
                if padre:
                    self.padre_id = padre.numero_cuenta
                    break
                posible_padre = posible_padre[:-1]

    def actualizar_saldo(self, debe=0, haber=0):
        """Actualiza el saldo de la cuenta"""
        if self.origen == 'DEBITO':
            self.saldo = float(self.saldo or 0) + (debe - haber)
        else:
            self.saldo = float(self.saldo or 0) + (haber - debe)

    @staticmethod
    def crear_o_actualizar_desde_excel(datos):
        """Crea o actualiza una cuenta desde datos de Excel"""
        cuenta = ContabilidadCuenta.query.filter_by(
            numero_cuenta=datos['numero_cuenta']
        ).first()

        if not cuenta:
            cuenta = ContabilidadCuenta()

        for key, value in datos.items():
            if hasattr(cuenta, key):
                setattr(cuenta, key, value)

        cuenta.calcular_nivel_y_padre()
        return cuenta

    def to_dict(self):
        """Convierte la cuenta a diccionario"""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'numero_cuenta': self.numero_cuenta,
            'nombre': self.nombre,
            'origen': self.origen,
            'categoria': self.categoria,
            'nivel': self.nivel,
            'padre_id': self.padre_id,
            'tipo': self.tipo,
            'grupo': self.grupo,
            'descripcion': self.descripcion,
            'estatus': self.estatus,
            'saldo': float(self.saldo) if self.saldo is not None else 0.0,
            'flujo_efectivo': self.flujo_efectivo,
            'corriente': self.corriente,
            'balance_general': self.balance_general,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }

    def __repr__(self):
        return f'<ContabilidadCuenta {self.numero_cuenta}: {self.nombre}>'

# Event listeners
@event.listens_for(ContabilidadCuenta, 'before_insert')
def cuenta_before_insert(mapper, connection, target):
    target.calcular_nivel_y_padre()

class AsientoDiario(db.Model):
    __tablename__ = 'asiento_diario'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    referencia = db.Column(db.String(50))
    cuenta_id = db.Column(db.Integer, db.ForeignKey('contabilidad_cuentas.id'), nullable=False)
    debe = db.Column(db.Numeric(precision=15, scale=2), default=0)
    haber = db.Column(db.Numeric(precision=15, scale=2), default=0)
    estado = db.Column(db.String(20), default='Pendiente')  # Pendiente, Aprobado, Anulado
    creado_por = db.Column(db.Integer)  # ID del usuario que creó el asiento
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cuenta = db.relationship('ContabilidadCuenta', back_populates='asientos')

    @validates('debe', 'haber')
    def validate_montos(self, key, value):
        """Valida que los montos sean números positivos"""
        try:
            valor = float(value or 0)
            if valor < 0:
                raise ValueError(f"El {key} no puede ser negativo")
            return valor
        except (TypeError, ValueError):
            raise FormatoInvalidoError(f"Valor inválido para {key}")

    def actualizar_saldos(self):
        """Actualiza los saldos en la cuenta afectada"""
        if self.cuenta:
            self.cuenta.actualizar_saldo(float(self.debe or 0), float(self.haber or 0))

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'descripcion': self.descripcion,
            'referencia': self.referencia,
            'cuenta_id': self.cuenta_id,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'debe': float(self.debe) if self.debe is not None else 0.0,
            'haber': float(self.haber) if self.haber is not None else 0.0,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

    def __repr__(self):
        return f'<AsientoDiario {self.id} - {self.descripcion}>'


class MayorGeneral(db.Model):
    __tablename__ = 'mayor_general'
    
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('contabilidad_cuentas.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    descripcion = db.Column(db.String(200))
    referencia = db.Column(db.String(50))
    debe = db.Column(db.Numeric(precision=15, scale=2), default=0)
    haber = db.Column(db.Numeric(precision=15, scale=2), default=0)
    saldo = db.Column(db.Numeric(precision=15, scale=2), default=0)
    asiento_id = db.Column(db.Integer, db.ForeignKey('asiento_diario.id'))

    cuenta = db.relationship('ContabilidadCuenta', back_populates='mayor')
    asiento = db.relationship('AsientoDiario')

    def calcular_saldo(self):
        """Calcula el saldo según el tipo de cuenta"""
        if self.cuenta.origen == 'DEBITO':
            self.saldo = float(self.debe or 0) - float(self.haber or 0)
        else:
            self.saldo = float(self.haber or 0) - float(self.debe or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'cuenta_id': self.cuenta_id,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'descripcion': self.descripcion,
            'referencia': self.referencia,
            'debe': float(self.debe) if self.debe is not None else 0.0,
            'haber': float(self.haber) if self.haber is not None else 0.0,
            'saldo': float(self.saldo) if self.saldo is not None else 0.0
        }

    def __repr__(self):
        return f'<MayorGeneral {self.cuenta.nombre if self.cuenta else "Sin cuenta"} - Saldo: {self.saldo}>'


class BalanzaComprobacion(db.Model):
    __tablename__ = 'balanza_comprobacion'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('contabilidad_cuentas.id'), nullable=False)
    saldo_inicial = db.Column(db.Numeric(precision=15, scale=2), default=0)
    debe = db.Column(db.Numeric(precision=15, scale=2), default=0)
    haber = db.Column(db.Numeric(precision=15, scale=2), default=0)
    saldo_final = db.Column(db.Numeric(precision=15, scale=2), default=0)
    periodo = db.Column(db.String(20))  # Mes/Año del período

    cuenta = db.relationship('ContabilidadCuenta', back_populates='balanza')

    def calcular_saldo_final(self):
        """Calcula el saldo final según el tipo de cuenta"""
        if self.cuenta.origen == 'DEBITO':
            self.saldo_final = float(self.saldo_inicial or 0) + float(self.debe or 0) - float(self.haber or 0)
        else:
            self.saldo_final = float(self.saldo_inicial or 0) + float(self.haber or 0) - float(self.debe or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'cuenta_id': self.cuenta_id,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'saldo_inicial': float(self.saldo_inicial) if self.saldo_inicial is not None else 0.0,
            'debe': float(self.debe) if self.debe is not None else 0.0,
            'haber': float(self.haber) if self.haber is not None else 0.0,
            'saldo_final': float(self.saldo_final) if self.saldo_final is not None else 0.0,
            'periodo': self.periodo
        }

    def __repr__(self):
        return f'<BalanzaComprobacion {self.cuenta.nombre if self.cuenta else "Sin cuenta"} - Período: {self.periodo}>'


class EstadoResultados(db.Model):
    __tablename__ = 'estado_resultados'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    periodo = db.Column(db.String(20))  # Mes/Año del período
    ingresos = db.Column(db.Numeric(precision=15, scale=2), default=0)
    costos = db.Column(db.Numeric(precision=15, scale=2), default=0)
    gastos = db.Column(db.Numeric(precision=15, scale=2), default=0)
    utilidad_bruta = db.Column(db.Numeric(precision=15, scale=2), default=0)
    utilidad_neta = db.Column(db.Numeric(precision=15, scale=2), default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def calcular_utilidades(self):
        """Calcula las utilidades bruta y neta"""
        self.utilidad_bruta = float(self.ingresos or 0) - float(self.costos or 0)
        self.utilidad_neta = self.utilidad_bruta - float(self.gastos or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'periodo': self.periodo,
            'ingresos': float(self.ingresos) if self.ingresos is not None else 0.0,
            'costos': float(self.costos) if self.costos is not None else 0.0,
            'gastos': float(self.gastos) if self.gastos is not None else 0.0,
            'utilidad_bruta': float(self.utilidad_bruta) if self.utilidad_bruta is not None else 0.0,
            'utilidad_neta': float(self.utilidad_neta) if self.utilidad_neta is not None else 0.0
        }

    def __repr__(self):
        return f'<EstadoResultados Período: {self.periodo} - Utilidad Neta: {self.utilidad_neta}>'


class BalanceGeneral(db.Model):
    __tablename__ = 'balance_general'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    periodo = db.Column(db.String(20))  # Mes/Año del período
    activos_circulantes = db.Column(db.Numeric(precision=15, scale=2), default=0)
    activos_fijos = db.Column(db.Numeric(precision=15, scale=2), default=0)
    total_activos = db.Column(db.Numeric(precision=15, scale=2), default=0)
    pasivos_corto_plazo = db.Column(db.Numeric(precision=15, scale=2), default=0)
    pasivos_largo_plazo = db.Column(db.Numeric(precision=15, scale=2), default=0)
    total_pasivos = db.Column(db.Numeric(precision=15, scale=2), default=0)
    capital_contable = db.Column(db.Numeric(precision=15, scale=2), default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def calcular_totales(self):
        """Calcula los totales del balance"""
        self.total_activos = float(self.activos_circulantes or 0) + float(self.activos_fijos or 0)
        self.total_pasivos = float(self.pasivos_corto_plazo or 0) + float(self.pasivos_largo_plazo or 0)
        self.capital_contable = self.total_activos - self.total_pasivos

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'periodo': self.periodo,
            'activos_circulantes': float(self.activos_circulantes) if self.activos_circulantes is not None else 0.0,
            'activos_fijos': float(self.activos_fijos) if self.activos_fijos is not None else 0.0,
            'total_activos': float(self.total_activos) if self.total_activos is not None else 0.0,
            'pasivos_corto_plazo': float(self.pasivos_corto_plazo) if self.pasivos_corto_plazo is not None else 0.0,
            'pasivos_largo_plazo': float(self.pasivos_largo_plazo) if self.pasivos_largo_plazo is not None else 0.0,
            'total_pasivos': float(self.total_pasivos) if self.total_pasivos is not None else 0.0,
            'capital_contable': float(self.capital_contable) if self.capital_contable is not None else 0.0
        }

    def __repr__(self):
        return f'<BalanceGeneral Período: {self.periodo} - Capital: {self.capital_contable}>'

# Event listeners para los cálculos automáticos
@event.listens_for(BalanzaComprobacion, 'before_insert')
@event.listens_for(BalanzaComprobacion, 'before_update')
def balanza_before_save(mapper, connection, target):
    target.calcular_saldo_final()

@event.listens_for(EstadoResultados, 'before_insert')
@event.listens_for(EstadoResultados, 'before_update')
def estado_resultados_before_save(mapper, connection, target):
    target.calcular_utilidades()

@event.listens_for(BalanceGeneral, 'before_insert')
@event.listens_for(BalanceGeneral, 'before_update')
def balance_general_before_save(mapper, connection, target):
    target.calcular_totales()    
    
# Agregar al final del archivo models.py

class Configuraciones(db.Model):
    __tablename__ = 'configuraciones'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # string, number, boolean, json
    grupo = db.Column(db.String(50))  # Grupo de configuración
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'clave': self.clave,
            'valor': self.valor,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'grupo': self.grupo,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None
        }

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        tipos_validos = ['string', 'number', 'boolean', 'json']
        if tipo and tipo not in tipos_validos:
            raise ValueError(f"Tipo debe ser uno de: {', '.join(tipos_validos)}")
        return tipo

    def __repr__(self):
        return f'<Configuraciones {self.clave}: {self.valor}>'


class FlujoCaja(db.Model):
    __tablename__ = 'flujo_caja'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    concepto = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # Ingreso/Egreso
    monto = db.Column(db.Numeric(precision=15, scale=2), nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('contabilidad_cuentas.id'))
    referencia = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='Pendiente')  # Pendiente, Aprobado, Anulado
    creado_por = db.Column(db.Integer)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cuenta = db.relationship('ContabilidadCuenta', backref=db.backref('flujos_caja', lazy=True))

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        if tipo and tipo.upper() not in ['INGRESO', 'EGRESO']:
            raise ValueError("El tipo debe ser INGRESO o EGRESO")
        return tipo.upper()

    @validates('monto')
    def validate_monto(self, key, monto):
        try:
            valor = float(monto)
            if valor <= 0:
                raise ValueError("El monto debe ser mayor que cero")
            return valor
        except (TypeError, ValueError):
            raise ValueError("Monto inválido")

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'concepto': self.concepto,
            'tipo': self.tipo,
            'monto': float(self.monto) if self.monto is not None else 0.0,
            'cuenta_id': self.cuenta_id,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'referencia': self.referencia,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

    def __repr__(self):
        return f'<FlujoCaja {self.concepto} - {self.tipo}: {self.monto}>'


# Agregar event listeners para FlujoCaja
@event.listens_for(FlujoCaja, 'after_insert')
def flujo_caja_after_insert(mapper, connection, target):
    """Actualiza el saldo de la cuenta después de insertar un flujo de caja"""
    if target.cuenta:
        monto = float(target.monto or 0)
        if target.tipo == 'INGRESO':
            target.cuenta.actualizar_saldo(debe=monto)
        else:
            target.cuenta.actualizar_saldo(haber=monto)

@event.listens_for(FlujoCaja, 'after_update')
def flujo_caja_after_update(mapper, connection, target):
    """Actualiza el saldo de la cuenta después de actualizar un flujo de caja"""
    if target.cuenta and hasattr(target, '_sa_initial_values'):
        monto_anterior = float(target._sa_initial_values.get('monto', 0) or 0)
        monto_nuevo = float(target.monto or 0)
        diferencia = monto_nuevo - monto_anterior
        
        if diferencia != 0:
            if target.tipo == 'INGRESO':
                target.cuenta.actualizar_saldo(debe=diferencia)
            else:
                target.cuenta.actualizar_saldo(haber=diferencia)    