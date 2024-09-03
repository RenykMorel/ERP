from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import mysql.connector

Base = declarative_base()

# Configuración de la base de datos
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/calculai_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Banco(Base):
    __tablename__ = "bancos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    contacto = Column(String(100))
    telefono_contacto = Column(String(20))
    estatus = Column(Enum("activo", "inactivo"), default="activo")

    @classmethod
    def obtener_todos(cls):
        db = SessionLocal()
        try:
            return db.query(cls).all()
        finally:
            db.close()

    @classmethod
    def buscar(cls, **kwargs):
        db = SessionLocal()
        try:
            query = db.query(cls)
            for key, value in kwargs.items():
                if value:
                    query = query.filter(getattr(cls, key).like(f"%{value}%"))
            return query.all()
        finally:
            db.close()

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "contacto": self.contacto,
            "telefono_contacto": self.telefono_contacto,
            "estatus": self.estatus,
        }


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50), nullable=False)
    monto = Column(Float, nullable=False)
    descripcion = Column(String(255))
    cuenta_id = Column(Integer)
    fecha_creacion = Column(DateTime)

    @classmethod
    def obtener_todos(cls):
        db = SessionLocal()
        try:
            return db.query(cls).all()
        finally:
            db.close()

    @classmethod
    def buscar(cls, **kwargs):
        db = SessionLocal()
        try:
            query = db.query(cls)
            for key, value in kwargs.items():
                if value:
                    query = query.filter(getattr(cls, key).like(f"%{value}%"))
            return query.all()
        finally:
            db.close()

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
        }


# Crear las tablas en la base de datos
Base.metadata.create_all(engine)
