from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Entidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class EmpresaMarketing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Agrega aquí otros campos que necesites para la empresa

class Prospecto(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    nombre = db.Column(db.String(64))
    apellido = db.Column(db.String(64))
    telefono = db.Column(db.String(20))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa_marketing.id'))
    asistente_activo = db.Column(db.Boolean, default=False)

    empresa = db.relationship('EmpresaMarketing', backref=db.backref('prospectos', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Prospecto {self.nombre_usuario}>'

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    company = db.Column(db.String(100))
    subscribed = db.Column(db.Boolean, default=True)
    prospecto_id = db.Column(db.Integer, db.ForeignKey('prospecto.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prospecto = db.relationship('Prospecto', backref=db.backref('contacts', lazy=True))

    def __repr__(self):
        return f'<Contact {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'subscribed': self.subscribed,
            'created_at': self.created_at.isoformat()
        }

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime)
    prospecto_id = db.Column(db.Integer, db.ForeignKey('prospecto.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prospecto = db.relationship('Prospecto', backref=db.backref('campaigns', lazy=True))

    def __repr__(self):
        return f'<Campaign {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'content': self.content,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat()
        }

class CampaignImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('prospecto.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campaign = db.relationship('Campaign', backref=db.backref('images', lazy=True))
    prospecto = db.relationship('Prospecto', backref=db.backref('created_images', lazy=True))

    def __repr__(self):
        return f'<CampaignImage {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'filepath': self.filepath,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }

class CampaignMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    opens = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    bounces = db.Column(db.Integer, default=0)
    unsubscribes = db.Column(db.Integer, default=0)

    campaign = db.relationship('Campaign', backref=db.backref('metrics', lazy=True))

    def __repr__(self):
        return f'<CampaignMetrics for Campaign {self.campaign_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'opens': self.opens,
            'clicks': self.clicks,
            'bounces': self.bounces,
            'unsubscribes': self.unsubscribes
        }