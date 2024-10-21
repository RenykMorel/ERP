from extensions import db
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy import event


class NuevoBanco(db.Model):
    __tablename__ = 'nuevo_bancos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    contacto = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estatus = db.Column(db.String(20), default='activo')
    direccion = db.Column(db.String(200))
    codigo = db.Column(db.String(20))
    codigo_swift = db.Column(db.String(20))
    fecha = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @validates('nombre', 'telefono')
    def validate_unique_fields(self, key, value):
        if key == 'nombre':
            existing = NuevoBanco.query.filter(NuevoBanco.nombre == value).first()
        elif key == 'telefono':
            existing = NuevoBanco.query.filter(NuevoBanco.telefono == value).first()
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
            'direccion': self.direccion,
            'codigo': self.codigo,
            'codigo_swift': self.codigo_swift,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['nombre', 'telefono', 'contacto', 'telefono_contacto', 'estatus', 'direccion', 'codigo', 'codigo_swift']
        return cls(**{k: v for k, v in data.items() if k in allowed_keys})

    def update_from_dict(self, data):
        allowed_keys = ['nombre', 'telefono', 'contacto', 'telefono_contacto', 'estatus', 'direccion', 'codigo', 'codigo_swift']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

    def __repr__(self):
        return f'<NuevoBanco {self.nombre}>'

class Divisa(db.Model):
    __tablename__ = 'divisas'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(3), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    tasa_cambio = db.Column(db.Float, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=func.now())
    abreviatura = db.Column(db.String(10))
    simbolo = db.Column(db.String(5))
    estatus = db.Column(db.String(20), default='activo')
    cuenta_por_cobrar = db.Column(db.String(50))
    cuenta_por_pagar = db.Column(db.String(50))
    prima_cxc = db.Column(db.String(50))
    prima_cxp = db.Column(db.String(50))
    ganancia_diferencia_cambiaria = db.Column(db.String(50))
    perdida_diferencia_cambiaria = db.Column(db.String(50))
    anticipo = db.Column(db.String(50))
    anticipo_prima = db.Column(db.String(50))
    anticipo_cxp = db.Column(db.String(50))
    anticipo_cxp_prima = db.Column(db.String(50))
    caja = db.Column(db.String(50))
    caja_prima = db.Column(db.String(50))
    nota_credito = db.Column(db.String(50))
    nota_credito_prima = db.Column(db.String(50))
    moneda_funcional = db.Column(db.Boolean, default=False)
    desglose = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'tasa_cambio': self.tasa_cambio,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'abreviatura': self.abreviatura,
            'simbolo': self.simbolo,
            'estatus': self.estatus,
            'cuenta_por_cobrar': self.cuenta_por_cobrar,
            'cuenta_por_pagar': self.cuenta_por_pagar,
            'prima_cxc': self.prima_cxc,
            'prima_cxp': self.prima_cxp,
            'ganancia_diferencia_cambiaria': self.ganancia_diferencia_cambiaria,
            'perdida_diferencia_cambiaria': self.perdida_diferencia_cambiaria,
            'anticipo': self.anticipo,
            'anticipo_prima': self.anticipo_prima,
            'anticipo_cxp': self.anticipo_cxp,
            'anticipo_cxp_prima': self.anticipo_cxp_prima,
            'caja': self.caja,
            'caja_prima': self.caja_prima,
            'nota_credito': self.nota_credito,
            'nota_credito_prima': self.nota_credito_prima,
            'moneda_funcional': self.moneda_funcional,
            'desglose': self.desglose
        }

    # ... (resto de los métodos)

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['codigo', 'nombre', 'tasa_cambio', 'abreviatura', 'simbolo', 'cuenta_por_cobrar', 'cuenta_por_pagar',
                        'prima_cxc', 'prima_cxp', 'ganancia_diferencia_cambiaria', 'perdida_diferencia_cambiaria',
                        'anticipo', 'anticipo_prima', 'anticipo_cxp', 'anticipo_cxp_prima', 'caja', 'caja_prima',
                        'nota_credito', 'nota_credito_prima', 'moneda_funcional', 'desglose']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['codigo', 'nombre', 'tasa_cambio', 'abreviatura', 'simbolo', 'cuenta_por_cobrar', 'cuenta_por_pagar',
                        'prima_cxc', 'prima_cxp', 'ganancia_diferencia_cambiaria', 'perdida_diferencia_cambiaria',
                        'anticipo', 'anticipo_prima', 'anticipo_cxp', 'anticipo_cxp_prima', 'caja', 'caja_prima',
                        'nota_credito', 'nota_credito_prima', 'moneda_funcional', 'desglose']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)
        self.fecha_actualizacion = func.now()

    def __repr__(self):
        return f'<Divisa {self.codigo} - {self.nombre}>'

class CuentaBancaria(db.Model):
    __tablename__ = 'cuentas_bancarias'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    tipo_cuenta = db.Column(db.String(20), nullable=False)
    estatus = db.Column(db.String(10), default='activo')
    
    banco = db.relationship('NuevoBanco', backref=db.backref('cuentas', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'nombre': self.nombre,
            'banco': self.banco.nombre,
            'tipo_cuenta': self.tipo_cuenta,
            'estatus': self.estatus
        }

class Deposito(db.Model):
    __tablename__ = 'depositos'
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    divisa_id = db.Column(db.Integer, db.ForeignKey('divisas.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    cuenta_bancaria = db.Column(db.String(50))
    numero = db.Column(db.String(50))
    concepto = db.Column(db.String(200))
    estatus = db.Column(db.String(20), default='nuevo')
    referencia = db.Column(db.String(50))
    creador = db.Column(db.String(100))
    actualizado_por = db.Column(db.String(100))
    fuente = db.Column(db.String(50))
    fuente_referencia = db.Column(db.String(50))
    
    banco = db.relationship('NuevoBanco', backref=db.backref('depositos', lazy=True))
    divisa = db.relationship('Divisa', backref=db.backref('depositos', lazy=True))

    def __repr__(self):
        return f'<Deposito {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'banco_id': self.banco_id,
            'divisa_id': self.divisa_id,
            'descripcion': self.descripcion,
            'cuenta_bancaria': self.cuenta_bancaria,
            'numero': self.numero,
            'concepto': self.concepto,
            'estatus': self.estatus,
            'referencia': self.referencia,
            'creador': self.creador,
            'actualizado_por': self.actualizado_por,
            'fuente': self.fuente,
            'fuente_referencia': self.fuente_referencia,
            'banco_nombre': self.banco.nombre if self.banco else None,
            'divisa_codigo': self.divisa.codigo if self.divisa else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'divisa_id', 'descripcion', 'cuenta_bancaria', 'numero',
                        'concepto', 'estatus', 'referencia', 'creador', 'actualizado_por', 'fuente', 'fuente_referencia']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'divisa_id', 'descripcion', 'cuenta_bancaria', 'numero',
                        'concepto', 'estatus', 'referencia', 'actualizado_por', 'fuente', 'fuente_referencia']
        for key, value in data.items():
            if key in allowed_keys:
                if key == 'fecha':
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)

    def __repr__(self):
        return f'<Deposito {self.id} - Banco {self.banco_id} - Divisa {self.divisa_id}>'

class CuentaAfectada(db.Model):
    __tablename__ = 'cuentas_afectadas'
    id = db.Column(db.Integer, primary_key=True)
    deposito_id = db.Column(db.Integer, db.ForeignKey('depositos.id'), nullable=False)
    identificador = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'debito' o 'credito'
    monto = db.Column(db.Float, nullable=False)

    deposito = db.relationship('Deposito', backref=db.backref('cuentas_afectadas', lazy=True))

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        if tipo not in ['debito', 'credito']:
            raise ValueError("El tipo debe ser 'debito' o 'credito'")
        return tipo

    def to_dict(self):
        return {
            'id': self.id,
            'deposito_id': self.deposito_id,
            'identificador': self.identificador,
            'tipo': self.tipo,
            'monto': self.monto
        }

class NotaCreditoDebito(db.Model):
    __tablename__ = 'notas_credito_debito'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # 'credito' o 'debito'
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    divisa_id = db.Column(db.Integer, db.ForeignKey('divisas.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    
    banco = db.relationship('NuevoBanco', backref=db.backref('notas_credito_debito', lazy=True))
    divisa = db.relationship('Divisa', backref=db.backref('notas_credito_debito', lazy=True))

    @validates('monto')
    def validate_monto(self, key, monto):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return monto

    @validates('tipo')
    def validate_tipo(self, key, tipo):
        if tipo not in ['credito', 'debito']:
            raise ValueError("El tipo debe ser 'credito' o 'debito'")
        return tipo

    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'banco_id': self.banco_id,
            'divisa_id': self.divisa_id,
            'descripcion': self.descripcion,
            'banco_nombre': self.banco.nombre if self.banco else None,
            'divisa_codigo': self.divisa.codigo if self.divisa else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['tipo', 'monto', 'fecha', 'banco_id', 'divisa_id', 'descripcion']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['tipo', 'monto', 'fecha', 'banco_id', 'divisa_id', 'descripcion']
        for key, value in data.items():
            if key in allowed_keys:
                if key == 'fecha':
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)

    def __repr__(self):
        return f'<NotaCreditoDebito {self.id} - Tipo {self.tipo} - Banco {self.banco_id}>'

class Transferencia(db.Model):
    __tablename__ = 'transferencias'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_origen_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    banco_destino_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    divisa_id = db.Column(db.Integer, db.ForeignKey('divisas.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    
    banco_origen = db.relationship('NuevoBanco', foreign_keys=[banco_origen_id])
    banco_destino = db.relationship('NuevoBanco', foreign_keys=[banco_destino_id])
    divisa = db.relationship('Divisa', backref=db.backref('transferencias', lazy=True))

    @validates('monto')
    def validate_monto(self, key, monto):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return monto

    @validates('banco_origen_id', 'banco_destino_id')
    def validate_diferentes_bancos(self, key, value):
        if key == 'banco_destino_id' and value == self.banco_origen_id:
            raise ValueError("El banco de origen y destino deben ser diferentes")
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'banco_origen_id': self.banco_origen_id,
            'banco_destino_id': self.banco_destino_id,
            'divisa_id': self.divisa_id,
            'descripcion': self.descripcion,
            'banco_origen_nombre': self.banco_origen.nombre if self.banco_origen else None,
            'banco_destino_nombre': self.banco_destino.nombre if self.banco_destino else None,
            'divisa_codigo': self.divisa.codigo if self.divisa else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['monto', 'fecha', 'banco_origen_id', 'banco_destino_id', 'divisa_id', 'descripcion']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['monto', 'fecha', 'banco_origen_id', 'banco_destino_id', 'divisa_id', 'descripcion']
        for key, value in data.items():
            if key in allowed_keys:
                if key == 'fecha':
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)

    def __repr__(self):
        return f'<Transferencia {self.id} - De: {self.banco_origen_id} A: {self.banco_destino_id}>'

class Conciliacion(db.Model):
    __tablename__ = 'conciliaciones'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    saldo_banco = db.Column(db.Float, nullable=False)
    saldo_libros = db.Column(db.Float, nullable=False)
    diferencia = db.Column(db.Float, nullable=False)
    
    banco = db.relationship('NuevoBanco', backref=db.backref('conciliaciones', lazy=True))

    @validates('saldo_banco', 'saldo_libros')
    def validate_saldos(self, key, value):
        if value < 0:
            raise ValueError(f"El {key.replace('_', ' ')} no puede ser negativo")
        return value

    def calcular_diferencia(self):
        self.diferencia = self.saldo_banco - self.saldo_libros

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'banco_id': self.banco_id,
            'saldo_banco': self.saldo_banco,
            'saldo_libros': self.saldo_libros,
            'diferencia': self.diferencia,
            'banco_nombre': self.banco.nombre if self.banco else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['fecha', 'banco_id', 'saldo_banco', 'saldo_libros']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        instance = cls(**filtered_data)
        instance.calcular_diferencia()
        return instance

    def update_from_dict(self, data):
        allowed_keys = ['fecha', 'banco_id', 'saldo_banco', 'saldo_libros']
        for key, value in data.items():
            if key in allowed_keys:
                if key == 'fecha':
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)
        self.calcular_diferencia()

    def __repr__(self):
        return f'<Conciliacion {self.id} - NuevoBanco {self.banco_id}>'

class Banco(db.Model):
    __tablename__ = 'bancos'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True)

    def __repr__(self):
        return f'<Banco {self.nombre}>'
    
class BancoCuenta(db.Model):
    __tablename__ = 'banco_cuentas'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    banco_id = db.Column(db.Integer, db.ForeignKey('bancos.id'), nullable=False)
    numero_cuenta = db.Column(db.String(50), nullable=False)
    tipo_cuenta = db.Column(db.String(50))
    saldo = db.Column(db.Numeric(precision=10, scale=2), default=0)
    
    banco = db.relationship('Banco', backref=db.backref('cuentas', lazy=True))

    def __repr__(self):
        return f'<BancoCuenta {self.numero_cuenta}>'

# Funciones auxiliares para conversiones de moneda
def convertir_moneda(monto: float, divisa_origen: Divisa, divisa_destino: Divisa) -> float:
    """
    Convierte un monto de una divisa a otra.
    
    :param monto: Cantidad a convertir
    :param divisa_origen: Divisa de origen
    :param divisa_destino: Divisa de destino
    :return: Monto convertido
    """
    if divisa_origen.codigo == divisa_destino.codigo:
        return monto
    
    # Convertimos primero a la moneda base (asumimos que es USD)
    monto_usd = monto / divisa_origen.tasa_cambio
    
    # Luego convertimos de USD a la moneda destino
    return monto_usd * divisa_destino.tasa_cambio

# Funciones para actualizar tasas de cambio (simuladas)
def actualizar_tasa_cambio(divisa: Divisa, nueva_tasa: float):
    """
    Actualiza la tasa de cambio de una divisa.
    
    :param divisa: Objeto Divisa a actualizar
    :param nueva_tasa: Nueva tasa de cambio
    """
    divisa.tasa_cambio = nueva_tasa
    divisa.fecha_actualizacion = func.now()
    db.session.commit()

def actualizar_tasas_desde_api():
    """
    Simula la actualización de tasas de cambio desde una API externa.
    En un escenario real, aquí se haría una llamada a una API de tasas de cambio.
    """
    # Simulación de datos de API
    tasas_api = {
        'USD': 1.0,
        'EUR': 0.85,
        'GBP': 0.73,
        'JPY': 110.21,
        # Añade más divisas según sea necesario
    }
    
    for codigo, tasa in tasas_api.items():
        divisa = Divisa.query.filter_by(codigo=codigo).first()
        if divisa:
            actualizar_tasa_cambio(divisa, tasa)
        else:
            nueva_divisa = Divisa(codigo=codigo, nombre=f"Moneda {codigo}", tasa_cambio=tasa)
            db.session.add(nueva_divisa)
    
    db.session.commit()

# Eventos de base de datos
@event.listens_for(Divisa, 'before_update')
def divisa_before_update(mapper, connection, target):
    target.fecha_actualizacion = func.now()

@event.listens_for(Conciliacion, 'before_insert')
@event.listens_for(Conciliacion, 'before_update')
def conciliacion_before_save(mapper, connection, target):
    target.calcular_diferencia()

# Función para inicializar las divisas básicas
def inicializar_divisas():
    divisas_base = [
        {'codigo': 'USD', 'nombre': 'Dólar estadounidense', 'tasa_cambio': 1.0},
        {'codigo': 'EUR', 'nombre': 'Euro', 'tasa_cambio': 0.85},
        {'codigo': 'GBP', 'nombre': 'Libra esterlina', 'tasa_cambio': 0.73},
        {'codigo': 'JPY', 'nombre': 'Yen japonés', 'tasa_cambio': 110.21},
    ]
    
    for divisa_data in divisas_base:
        if not Divisa.query.filter_by(codigo=divisa_data['codigo']).first():
            nueva_divisa = Divisa(**divisa_data)
            db.session.add(nueva_divisa)
    
    db.session.commit()

# Esta función debe ser llamada después de crear todas las tablas
# db.create_all()
# inicializar_divisas()