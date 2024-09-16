from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Table, ForeignKey, Boolean, JSON, event
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()

# Función para notificar al asistente (simulada)
def notificar_asistente(mensaje):
    print(f"Notificación al asistente: {mensaje}")
    # Aquí se implementaría la lógica real para notificar al asistente

# Tablas de asociación
usuario_roles = Table(
    "usuario_roles",
    db.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id")),
    Column("rol_id", Integer, ForeignKey("roles.id")),
)

usuario_modulos = Table(
    "usuario_modulos",
    db.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id")),
    Column("modulo_id", Integer, ForeignKey("modulos.id")),
)

rol_permisos = Table(
    "rol_permisos",
    db.metadata,
    Column("rol_id", Integer, ForeignKey("roles.id")),
    Column("permiso_id", Integer, ForeignKey("permisos.id")),
)

usuario_empresa = Table(
    "usuario_empresa",
    db.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id"), primary_key=True),
    Column("empresa_id", Integer, ForeignKey("empresas.id"), primary_key=True),
    Column("rol_en_empresa", String(50)),
)

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nombre_usuario = Column(String(64), index=True, unique=True, nullable=False)
    email = Column(String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    es_admin = Column(Boolean, default=False)
    es_super_admin = Column(Boolean, default=False)
    rol = Column(String(20), default="usuario")
    estado = Column(String(20), default="activo")
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    roles = relationship("Rol", secondary=usuario_roles, back_populates="usuarios")
    modulos = relationship("Modulo", secondary=usuario_modulos, back_populates="usuarios")
    empresas = relationship("Empresa", secondary=usuario_empresa, back_populates="usuarios")
    notificaciones = relationship("Notificacion", back_populates="usuario")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_email(email):
        return Usuario.query.filter_by(email=email).first()

    def to_dict(self):
        return {
            "id": self.id,
            "nombre_usuario": self.nombre_usuario,
            "email": self.email,
            "es_admin": self.es_admin,
            "es_super_admin": self.es_super_admin,
            "estado": self.estado,
            "rol": self.rol,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
        }

class Empresa(db.Model):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    estado = Column(String(20), default="activo")
    usuarios = relationship("Usuario", secondary=usuario_empresa, back_populates="empresas")

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre, "estado": self.estado}

class Rol(db.Model):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    usuarios = relationship("Usuario", secondary=usuario_roles, back_populates="roles")
    permisos = relationship("Permiso", secondary=rol_permisos, back_populates="roles")
    permisos_json = Column(JSON)

class Permiso(db.Model):
    __tablename__ = "permisos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    roles = relationship("Rol", secondary=rol_permisos, back_populates="permisos")

class Modulo(db.Model):
    __tablename__ = "modulos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    modulo_padre_id = Column(Integer, ForeignKey("modulos.id"))
    usuarios = relationship("Usuario", secondary=usuario_modulos, back_populates="modulos")
    submodulos = relationship("Modulo", backref=db.backref('padre', remote_side=[id]))

class UsuarioModulo(db.Model):
    __tablename__ = "usuario_modulo"
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    modulo_id = Column(Integer, ForeignKey("modulos.id"), primary_key=True)
    permisos = Column(JSON)
    usuario = relationship("Usuario", backref=db.backref("usuario_modulos", cascade="all, delete-orphan"))
    modulo = relationship("Modulo", backref=db.backref("usuario_modulos", cascade="all, delete-orphan"))

class Notificacion(db.Model):
    __tablename__ = "notificaciones"
    id = Column(Integer, primary_key=True)
    mensaje = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    leida = Column(Boolean, default=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario", back_populates="notificaciones")

class Banco(db.Model):
    __tablename__ = "bancos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    contacto = Column(String(100))
    telefono_contacto = Column(String(20))
    estatus = Column(Enum("activo", "inactivo", name="banco_estatus_enum"), default="activo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def obtener_todos(cls):
        bancos = cls.query.all()
        notificar_asistente(f"Se han recuperado {len(bancos)} bancos de la base de datos.")
        return bancos

    @classmethod
    def buscar(cls, **kwargs):
        query = cls.query
        for key, value in kwargs.items():
            if value:
                query = query.filter(getattr(cls, key).ilike(f"%{value}%"))
        resultados = query.all()
        notificar_asistente(f"Búsqueda de bancos realizada con {len(resultados)} resultados. Criterios: {kwargs}")
        return resultados

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "contacto": self.contacto,
            "telefono_contacto": self.telefono_contacto,
            "estatus": self.estatus,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

class Transaccion(db.Model):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50), nullable=False)
    monto = Column(Float, nullable=False)
    descripcion = Column(String(255))
    cuenta_id = Column(Integer)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def obtener_todos(cls):
        transacciones = cls.query.all()
        notificar_asistente(f"Se han recuperado {len(transacciones)} transacciones de la base de datos.")
        return transacciones

    @classmethod
    def buscar(cls, **kwargs):
        query = cls.query
        for key, value in kwargs.items():
            if value:
                query = query.filter(getattr(cls, key).ilike(f"%{value}%"))
        resultados = query.all()
        notificar_asistente(f"Búsqueda de transacciones realizada con {len(resultados)} resultados. Criterios: {kwargs}")
        return resultados

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "monto": self.monto,
            "descripcion": self.descripcion,
            "cuenta_id": self.cuenta_id,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

# Eventos para notificar al asistente sobre operaciones en la base de datos
@event.listens_for(Banco, "after_insert")
def notify_banco_insert(mapper, connection, target):
    notificar_asistente(f"Nuevo banco creado: {target.nombre}")

@event.listens_for(Banco, "after_update")
def notify_banco_update(mapper, connection, target):
    notificar_asistente(f"Banco actualizado: {target.nombre}")

@event.listens_for(Transaccion, "after_insert")
def notify_transaccion_insert(mapper, connection, target):
    notificar_asistente(f"Nueva transacción creada: {target.tipo} por {target.monto}")

@event.listens_for(Transaccion, "after_update")
def notify_transaccion_update(mapper, connection, target):
    notificar_asistente(f"Transacción actualizada: {target.tipo} por {target.monto}")