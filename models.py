from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"  # Explícitamente establecemos el nombre de la tabla
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    status = db.Column(db.String(20), default="active")
    role = db.Column(db.String(20), default="user")
    companies = db.relationship(
        "Company", secondary="user_company", back_populates="users"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "status": self.status,
            "role": self.role,
        }


class Company(db.Model):
    __tablename__ = "company"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="active")
    users = db.relationship(
        "User", secondary="user_company", back_populates="companies"
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name, "status": self.status}


user_company = db.Table(
    "user_company",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("company_id", db.Integer, db.ForeignKey("company.id"), primary_key=True),
    db.Column("role_in_company", db.String(50)),
)


class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.JSON)


class Module(db.Model):
    __tablename__ = "module"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    parent_module_id = db.Column(db.Integer, db.ForeignKey("module.id"))
    parent = db.relationship("Module", remote_side=[id], backref="submodules")


class UserModule(db.Model):
    __tablename__ = "user_module"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("module.id"), primary_key=True)
    permissions = db.Column(db.JSON)
    user = db.relationship(
        "User", backref=db.backref("user_modules", cascade="all, delete-orphan")
    )
    module = db.relationship(
        "Module", backref=db.backref("user_modules", cascade="all, delete-orphan")
    )


class Banco(db.Model):
    __tablename__ = "banco"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    contacto = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estatus = db.Column(db.Enum("activo", "inactivo"), default="activo")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "contacto": self.contacto,
            "telefono_contacto": self.telefono_contacto,
            "estatus": self.estatus,
        }


class Transaccion(db.Model):
    __tablename__ = "transaccion"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255))
    cuenta_id = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "monto": self.monto,
            "descripcion": self.descripcion,
            "cuenta_id": self.cuenta_id,
        }


class Company(db.Model):
    __tablename__ = "company"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="active")
    users = db.relationship(
        "User", secondary="user_company", back_populates="companies"
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name, "status": self.status}


user_company = db.Table(
    "user_company",
    db.Column("user_id", db.Integer, db.ForeignKey("usuario.id"), primary_key=True),
    db.Column("company_id", db.Integer, db.ForeignKey("company.id"), primary_key=True),
    db.Column("role_in_company", db.String(50)),
)


class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.JSON)


class Module(db.Model):
    __tablename__ = "module"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    parent_module_id = db.Column(db.Integer, db.ForeignKey("module.id"))
    parent = db.relationship("Module", remote_side=[id], backref="submodules")


class UserModule(db.Model):
    __tablename__ = "user_module"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("module.id"), primary_key=True)
    permissions = db.Column(db.JSON)
    user = db.relationship(
        "User", backref=db.backref("user_modules", cascade="all, delete-orphan")
    )
    module = db.relationship(
        "Module", backref=db.backref("user_modules", cascade="all, delete-orphan")
    )


class Banco(db.Model):
    __tablename__ = "banco"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    contacto = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estatus = db.Column(db.Enum("activo", "inactivo"), default="activo")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "contacto": self.contacto,
            "telefono_contacto": self.telefono_contacto,
            "estatus": self.estatus,
        }


class Transaccion(db.Model):
    __tablename__ = "transaccion"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255))
    cuenta_id = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "monto": self.monto,
            "descripcion": self.descripcion,
            "cuenta_id": self.cuenta_id,
        }
