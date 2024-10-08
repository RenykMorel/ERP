from extensions import db
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy import event

class NuevoBanco(db.Model):
    __tablename__ = 'nuevo_bancos'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    contacto = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estatus = db.Column(db.String(20), default='activo')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

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
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['nombre', 'telefono', 'contacto', 'telefono_contacto', 'estatus']
        return cls(**{k: v for k, v in data.items() if k in allowed_keys})

    def update_from_dict(self, data):
        allowed_keys = ['nombre', 'telefono', 'contacto', 'telefono_contacto', 'estatus']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)

    def __repr__(self):
        return f'<NuevoBanco {self.nombre}>'



class NotaCreditoBanco(db.Model):
    __tablename__ = 'notas_credito_banco'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    
    banco = db.relationship('NuevoBanco', backref=db.backref('notas_credito_banco', lazy=True))

    @validates('monto')
    def validate_monto(self, key, monto):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return monto

    def to_dict(self):
        return {
            'id': self.id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'banco_id': self.banco_id,
            'descripcion': self.descripcion,
            'banco_nombre': self.banco.nombre if self.banco else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'descripcion']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'descripcion']
        for key, value in data.items():
            if key in allowed_keys:
                if key == 'fecha':
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)

    def __repr__(self):
        return f'<NotaCredito {self.id} - NuevoBanco {self.banco_id}>'

class NotaDebitoBanco(db.Model):
    __tablename__ = 'notas_debito_banco'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    
    banco = db.relationship('NuevoBanco', backref=db.backref('notas_debito_banco', lazy=True))

    @validates('monto')
    def validate_monto(self, key, monto):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return monto

    def to_dict(self):
        return {
            'id': self.id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'banco_id': self.banco_id,
            'descripcion': self.descripcion,
            'banco_nombre': self.banco.nombre if self.banco else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'descripcion']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'descripcion']
        for key, value in data.items():
            if key in allowed_keys:
                if key == 'fecha':
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)

    def __repr__(self):
        return f'<NotaDebitoBanco {self.id} - NuevoBanco {self.banco_id}>'

class Transferencia(db.Model):
    __tablename__ = 'transferencias'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_origen_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    banco_destino_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    
    banco_origen = db.relationship('NuevoBanco', foreign_keys=[banco_origen_id])
    banco_destino = db.relationship('NuevoBanco', foreign_keys=[banco_destino_id])

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
            'descripcion': self.descripcion,
            'banco_origen_nombre': self.banco_origen.nombre if self.banco_origen else None,
            'banco_destino_nombre': self.banco_destino.nombre if self.banco_destino else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['monto', 'fecha', 'banco_origen_id', 'banco_destino_id', 'descripcion']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['monto', 'fecha', 'banco_origen_id', 'banco_destino_id', 'descripcion']
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

class Deposito(db.Model):
    __tablename__ = 'depositos'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    banco_id = db.Column(db.Integer, db.ForeignKey('nuevo_bancos.id'), nullable=False)
    descripcion = db.Column(db.String(200))
    
    banco = db.relationship('NuevoBanco', backref=db.backref('depositos', lazy=True))

    @validates('monto')
    def validate_monto(self, key, monto):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return monto

    def to_dict(self):
        return {
            'id': self.id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'banco_id': self.banco_id,
            'descripcion': self.descripcion,
            'banco_nombre': self.banco.nombre if self.banco else None
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'descripcion']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        if 'fecha' in filtered_data:
            filtered_data['fecha'] = datetime.fromisoformat(filtered_data['fecha'])
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['monto', 'fecha', 'banco_id', 'descripcion']
        for key, value in data.items():
            if key in allowed_keys:
                if key == 'fecha':
                    value = datetime.fromisoformat(value)
                setattr(self, key, value)

    def __repr__(self):
        return f'<Deposito {self.id} - Banco {self.banco_id}>'

class Divisa(db.Model):
    __tablename__ = 'divisas'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(3), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    tasa_cambio = db.Column(db.Float, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=func.now())

    @validates('codigo')
    def validate_codigo(self, key, codigo):
        if len(codigo) != 3:
            raise ValueError("El código de la divisa debe tener exactamente 3 caracteres")
        return codigo.upper()

    @validates('tasa_cambio')
    def validate_tasa_cambio(self, key, tasa_cambio):
        if tasa_cambio <= 0:
            raise ValueError("La tasa de cambio debe ser mayor que cero")
        return tasa_cambio

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'tasa_cambio': self.tasa_cambio,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        allowed_keys = ['codigo', 'nombre', 'tasa_cambio']
        filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered_data)

    def update_from_dict(self, data):
        allowed_keys = ['codigo', 'nombre', 'tasa_cambio']
        for key, value in data.items():
            if key in allowed_keys:
                setattr(self, key, value)
        self.fecha_actualizacion = func.now()

    def __repr__(self):
        return f'<Divisa {self.codigo} - {self.nombre}>'

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