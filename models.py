from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Table, ForeignKey, Boolean, JSON, event, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.exc import IntegrityError

db = SQLAlchemy()

def notificar_asistente(mensaje):
    print(f"Notificación al asistente: {mensaje}")
    # Aquí se implementaría la lógica real para notificar al asistente

# Tablas de asociación existentes
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

# Modelos existentes
class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nombre_usuario = Column(String(64), index=True, unique=True, nullable=False)
    email = Column(String(120), index=True, unique=True, nullable=False)
    password_hash = Column(String(500), nullable=False)
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

    @classmethod
    def crear_usuario(cls, nombre_usuario, email, password, es_admin=False, es_super_admin=False, rol="usuario"):
        nuevo_usuario = cls(
            nombre_usuario=nombre_usuario,
            email=email,
            es_admin=es_admin,
            es_super_admin=es_super_admin,
            rol=rol
        )
        nuevo_usuario.set_password(password)
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            notificar_asistente(f"Nuevo usuario creado: {nombre_usuario}")
            return nuevo_usuario
        except IntegrityError:
            db.session.rollback()
            raise ValueError("El nombre de usuario o email ya existe")
        except Exception as e:
            db.session.rollback()
            raise e

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
    rnc = Column(String(20), unique=True)
    direccion = Column(String(200))
    tipo = Column(String(50))
    representante = Column(String(100))
    estado = Column(String(20), default="activo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    usuarios = relationship("Usuario", secondary=usuario_empresa, back_populates="empresas")

    @classmethod
    def crear_empresa(cls, nombre, rnc, direccion):
        nueva_empresa = cls(nombre=nombre, rnc=rnc, direccion=direccion)
        try:
            db.session.add(nueva_empresa)
            db.session.flush()  # Esto asigna un ID a nueva_empresa sin hacer commit
            return nueva_empresa
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f"Ya existe una empresa con ese RNC o nombre: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error al crear la empresa: {str(e)}")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "rnc": self.rnc,
            "direccion": self.direccion,
            "tipo": self.tipo,
            "representante": self.representante,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

class Rol(db.Model):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    usuarios = relationship("Usuario", secondary=usuario_roles, back_populates="roles")
    permisos = relationship("Permiso", secondary=rol_permisos, back_populates="roles")
    permisos_json = Column(JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "permisos_json": self.permisos_json
        }

class Permiso(db.Model):
    __tablename__ = "permisos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    roles = relationship("Rol", secondary=rol_permisos, back_populates="permisos")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre
        }

class Modulo(db.Model):
    __tablename__ = "modulos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    modulo_padre_id = Column(Integer, ForeignKey("modulos.id"))
    usuarios = relationship("Usuario", secondary=usuario_modulos, back_populates="modulos")
    submodulos = relationship("Modulo", backref=db.backref('padre', remote_side=[id]))

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "modulo_padre_id": self.modulo_padre_id
        }

class UsuarioModulo(db.Model):
    __tablename__ = "usuario_modulo"
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    modulo_id = Column(Integer, ForeignKey("modulos.id"), primary_key=True)
    permisos = Column(JSON)
    usuario = relationship("Usuario", backref=db.backref("usuario_modulos", cascade="all, delete-orphan"))
    modulo = relationship("Modulo", backref=db.backref("usuario_modulos", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "usuario_id": self.usuario_id,
            "modulo_id": self.modulo_id,
            "permisos": self.permisos
        }

class Notificacion(db.Model):
    __tablename__ = "notificaciones"
    id = Column(Integer, primary_key=True)
    mensaje = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    leida = Column(Boolean, default=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario", back_populates="notificaciones")

    def to_dict(self):
        return {
            "id": self.id,
            "mensaje": self.mensaje,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "leida": self.leida,
            "usuario_id": self.usuario_id
        }

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
    cuenta_id = Column(Integer, ForeignKey("cuentas.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cuenta = relationship("Cuenta", back_populates="transacciones")

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

class Cuenta(db.Model):
    __tablename__ = "cuentas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(50), unique=True, nullable=False)
    tipo = Column(String(50), nullable=False)
    saldo = Column(Float, default=0.0)
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    banco = relationship("Banco", backref="cuentas")
    usuario = relationship("Usuario", backref="cuentas")
    transacciones = relationship("Transaccion", back_populates="cuenta")

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "tipo": self.tipo,
            "saldo": self.saldo,
            "banco_id": self.banco_id,
            "usuario_id": self.usuario_id,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

# Nuevos modelos para el panel de administración
class AdminPlanSuscripcion(db.Model):
    __tablename__ = "admin_planes_suscripcion"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float, nullable=False)
    duracion_dias = Column(Integer, nullable=False)
    caracteristicas = Column(JSON)
    estado = Column(String(20), default="activo")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio": self.precio,
            "duracion_dias": self.duracion_dias,
            "caracteristicas": self.caracteristicas,
            "estado": self.estado,
        }

class AdminFactura(db.Model):
    __tablename__ = "admin_facturas"
    id = Column(Integer, primary_key=True)
    numero_factura = Column(String(50), unique=True, nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    monto = Column(Float, nullable=False)
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento = Column(DateTime)
    estado = Column(String(20), default="pendiente")

    empresa = relationship("Empresa", backref="facturas")

    def to_dict(self):
        return {
            "id": self.id,
            "numero_factura": self.numero_factura,
            "empresa_id": self.empresa_id,
            "monto": self.monto,
            "fecha_emision": self.fecha_emision.isoformat() if self.fecha_emision else None,
            "fecha_vencimiento": self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            "estado": self.estado,
        }

class AdminConfiguracionSeguridad(db.Model):
    __tablename__ = "admin_configuracion_seguridad"
    id = Column(Integer, primary_key=True)
    clave = Column(String(50), unique=True, nullable=False)
    valor = Column(Text)
    descripcion = Column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "clave": self.clave,
            "valor": self.valor,
            "descripcion": self.descripcion,
        }

class AdminReporte(db.Model):
    __tablename__ = "admin_reportes"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(50), nullable=False)
    parametros = Column(JSON)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    usuario = relationship("Usuario", backref="reportes")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "parametros": self.parametros,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "usuario_id": self.usuario_id,
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

@event.listens_for(Cuenta, "after_insert")
def notify_cuenta_insert(mapper, connection, target):
    notificar_asistente(f"Nueva cuenta creada: {target.numero}")

@event.listens_for(Cuenta, "after_update")
def notify_cuenta_update(mapper, connection, target):
    notificar_asistente(f"Cuenta actualizada: {target.numero}")

@event.listens_for(Usuario, "after_insert")
def notify_usuario_insert(mapper, connection, target):
    notificar_asistente(f"Nuevo usuario creado: {target.nombre_usuario}")

@event.listens_for(Usuario, "after_update")
def notify_usuario_update(mapper, connection, target):
    notificar_asistente(f"Usuario actualizado: {target.nombre_usuario}")

@event.listens_for(Empresa, "after_insert")
def notify_empresa_insert(mapper, connection, target):
    notificar_asistente(f"Nueva empresa creada: {target.nombre}")

@event.listens_for(Empresa, "after_update")
def notify_empresa_update(mapper, connection, target):
    notificar_asistente(f"Empresa actualizada: {target.nombre}")

# Nuevos eventos para los modelos de administración
@event.listens_for(AdminPlanSuscripcion, "after_insert")
def notify_plan_suscripcion_insert(mapper, connection, target):
    notificar_asistente(f"Nuevo plan de suscripción creado: {target.nombre}")

@event.listens_for(AdminPlanSuscripcion, "after_update")
def notify_plan_suscripcion_update(mapper, connection, target):
    notificar_asistente(f"Plan de suscripción actualizado: {target.nombre}")

@event.listens_for(AdminFactura, "after_insert")
def notify_factura_insert(mapper, connection, target):
    notificar_asistente(f"Nueva factura creada: {target.numero_factura}")

@event.listens_for(AdminFactura, "after_update")
def notify_factura_update(mapper, connection, target):
    notificar_asistente(f"Factura actualizada: {target.numero_factura}")

@event.listens_for(AdminConfiguracionSeguridad, "after_update")
def notify_configuracion_seguridad_update(mapper, connection, target):
    notificar_asistente(f"Configuración de seguridad actualizada: {target.clave}")

@event.listens_for(AdminReporte, "after_insert")
def notify_reporte_insert(mapper, connection, target):
    notificar_asistente(f"Nuevo reporte creado: {target.nombre}")

@event.listens_for(AdminReporte, "after_update")
def notify_reporte_update(mapper, connection, target):
    notificar_asistente(f"Reporte actualizado: {target.nombre}")