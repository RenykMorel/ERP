from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    nombre = db.Column(db.String(64))
    apellido = db.Column(db.String(64))
    telefono = db.Column(db.String(20))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    rol = db.Column(db.String(20))
    asistente_activo = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(64), index=True, unique=True)
    rnc = db.Column(db.String(20), unique=True)
    direccion = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    estado = db.Column(db.String(20))
    usuarios = db.relationship('Usuario', backref='empresa', lazy='dynamic')

    def __repr__(self):
        return f'<Empresa {self.nombre}>'

class Rol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)
    descripcion = db.Column(db.String(200))

    def __repr__(self):
        return f'<Rol {self.nombre}>'

class Permiso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)
    descripcion = db.Column(db.String(200))

    def __repr__(self):
        return f'<Permiso {self.nombre}>'

class Modulo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)
    descripcion = db.Column(db.String(200))

    def __repr__(self):
        return f'<Modulo {self.nombre}>'

class UsuarioModuloBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulo.id'))
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<UsuarioModulo {self.id}>'

class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    mensaje = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    leida = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Notificacion {self.id}>'

class Transaccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))
    monto = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.String(200))
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'))

    def __repr__(self):
        return f'<Transaccion {self.id}>'

class Cuenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    saldo = db.Column(db.Float)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))

    def __repr__(self):
        return f'<Cuenta {self.nombre}>'

class AdminPlanSuscripcion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    descripcion = db.Column(db.String(200))
    precio = db.Column(db.Float)
    duracion = db.Column(db.Integer)  # en días

    def __repr__(self):
        return f'<AdminPlanSuscripcion {self.nombre}>'

class AdminFactura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    monto = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20))

    def __repr__(self):
        return f'<AdminFactura {self.id}>'

class AdminConfiguracionSeguridadBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    politica_contrasenas = db.Column(db.String(200))
    tiempo_sesion = db.Column(db.Integer)  # en minutos
    intentos_login = db.Column(db.Integer)

    def __repr__(self):
        return f'<AdminConfiguracionSeguridad {self.id}>'

class AdminReporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    contenido = db.Column(db.Text)

    def __repr__(self):
        return f'<AdminReporte {self.id}>'

class Conversacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    contenido = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Conversacion {self.id}>'

class ContextoAsistente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    contexto = db.Column(db.Text, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ContextoAsistente {self.id}>'