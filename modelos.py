from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, event
from datetime import datetime
from sqlalchemy import text


db = SQLAlchemy()

# Configuración de la base de datos
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/calculai_db"


# Función para notificar al asistente (simulada)
def notificar_asistente(mensaje):
    print(f"Notificación al asistente: {mensaje}")
    # Aquí se implementaría la lógica real para notificar al asistente


class Banco(db.Model):
    __tablename__ = "bancos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    contacto = Column(String(100))
    telefono_contacto = Column(String(20))
    estatus = Column(Enum("activo", "inactivo"), default="activo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @classmethod
    def obtener_todos(cls):
        bancos = cls.query.all()
        notificar_asistente(
            f"Se han recuperado {len(bancos)} bancos de la base de datos."
        )
        return bancos

    @classmethod
    def buscar(cls, **kwargs):
        query = cls.query
        for key, value in kwargs.items():
            if value:
                query = query.filter(getattr(cls, key).like(f"%{value}%"))
        resultados = query.all()
        notificar_asistente(
            f"Búsqueda de bancos realizada con {len(resultados)} resultados. Criterios: {kwargs}"
        )
        return resultados

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "contacto": self.contacto,
            "telefono_contacto": self.telefono_contacto,
            "estatus": self.estatus,
            "fecha_creacion": (
                self.fecha_creacion.isoformat() if self.fecha_creacion else None
            ),
            "fecha_actualizacion": (
                self.fecha_actualizacion.isoformat()
                if self.fecha_actualizacion
                else None
            ),
        }


class Transaccion(db.Model):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50), nullable=False)
    monto = Column(Float, nullable=False)
    descripcion = Column(String(255))
    cuenta_id = Column(Integer)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @classmethod
    def obtener_todos(cls):
        transacciones = cls.query.all()
        notificar_asistente(
            f"Se han recuperado {len(transacciones)} transacciones de la base de datos."
        )
        return transacciones

    @classmethod
    def buscar(cls, **kwargs):
        query = cls.query
        for key, value in kwargs.items():
            if value:
                query = query.filter(getattr(cls, key).like(f"%{value}%"))
        resultados = query.all()
        notificar_asistente(
            f"Búsqueda de transacciones realizada con {len(resultados)} resultados. Criterios: {kwargs}"
        )
        return resultados

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "monto": self.monto,
            "descripcion": self.descripcion,
            "cuenta_id": self.cuenta_id,
            "fecha_creacion": (
                self.fecha_creacion.isoformat() if self.fecha_creacion else None
            ),
            "fecha_actualizacion": (
                self.fecha_actualizacion.isoformat()
                if self.fecha_actualizacion
                else None
            ),
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


def init_db(app):
    with app.app_context():
        connection = db.engine.connect()
        connection.execute(text("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"))
        db.create_all()
        connection.close()
