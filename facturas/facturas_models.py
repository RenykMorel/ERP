from extensions import db
from sqlalchemy import event, func
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func, text
from datetime import datetime
from common.models import ItemFactura, ItemPreFactura, MovimientoInventario
from flask import current_app
from flask_login import current_user
import os
import base64
import requests
import time
import random 


class Facturacion(db.Model):
  __tablename__ = 'facturacion'
  __table_args__ = {'extend_existing': True}
  
  id = db.Column(db.Integer, primary_key=True)
  numero = db.Column(db.String(50), unique=True, nullable=False)
  cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
  fecha = db.Column(db.Date, nullable=False)
  total = db.Column(db.Float, nullable=False)
  estatus = db.Column(db.String(20), default='pendiente')
  fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
  fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())
  
  tipo = db.Column(db.String(20), nullable=False, default='contado')
  tipo_pago = db.Column(db.String(20), nullable=False, default='efectivo')
  moneda = db.Column(db.String(10), nullable=False, default='DOP')
  tienda_id = db.Column(db.Integer, db.ForeignKey('tiendafactura.id'), nullable=False)
  vendedor_id = db.Column(db.Integer, db.ForeignKey('vendedores.id'), nullable=False)
  
  descuento_monto = db.Column(db.Float, default=0)
  descuento_porcentaje = db.Column(db.Float, default=0)
  notas = db.Column(db.Text)

  TIPOS_VALIDOS = ['contado', 'credito']
  TIPOS_PAGO_VALIDOS = ['efectivo', 'tarjeta', 'transferencia', 'cheque']
  MONEDAS_VALIDAS = ['DOP', 'USD']
  ESTATUS_VALIDOS = ['pendiente', 'pagada', 'anulada', 'vencida']

  # Relaciones actualizadas 
  items = db.relationship(
      'ItemFactura',
      back_populates='factura',
      lazy=True,
      cascade='all, delete-orphan'
  )
  
  cliente = db.relationship(
      'Cliente',
      backref=db.backref('facturas', lazy=True)
  )
  
  tienda = db.relationship(
      'TiendaFactura',
      foreign_keys=[tienda_id],
      back_populates='facturas', 
      lazy=True
  )
  
  vendedor = db.relationship('Vendedor')
  
  notas_credito = db.relationship(
      'NotaCredito',
      backref='factura',
      lazy=True,
      cascade='all, delete-orphan'
  )
  
  notas_debito = db.relationship(
      'NotaDebito',
      backref='factura',
      lazy=True,
      cascade='all, delete-orphan'
  )

  def __init__(self, **kwargs):
      super(Facturacion, self).__init__(**kwargs)
      self._items_procesados = False



@classmethod
def before_commit(cls, session):
    """Evento antes del commit"""
    for obj in session.new:
        if isinstance(obj, cls):
            try:
                for item in obj.items:
                    item.procesar_inventario()
            except ValueError as e:
                if isinstance(e.args[0], dict) and e.args[0].get("error") == "stock_insuficiente":
                    raise
                print(f"ERROR en before_commit: {str(e)}")
                raise

@classmethod
def __declare_last__(cls):
    """Registrar eventos de SQLAlchemy"""
    event.listen(db.session, 'before_commit', cls.before_commit)

@validates('numero')
def validate_unique_numero(self, key, value):
    if value is None:
        raise ValueError("El número de factura no puede ser nulo")
    if self.id is None:
        existing = Facturacion.query.filter(
            Facturacion.numero == value
        ).first()
        if existing:
            raise IntegrityError("Número de factura ya existe", value, '')
    return value

@validates('estatus')
def validate_estatus(self, key, estatus):
    if estatus not in self.ESTATUS_VALIDOS:
        raise ValueError(f"Estatus inválido. Debe ser uno de: {', '.join(self.ESTATUS_VALIDOS)}")
    return estatus

@validates('tipo')
def validate_tipo(self, key, tipo):
    if tipo not in self.TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido. Debe ser uno de: {', '.join(self.TIPOS_VALIDOS)}")
    return tipo

@validates('tipo_pago')
def validate_tipo_pago(self, key, tipo_pago):
    if tipo_pago not in self.TIPOS_PAGO_VALIDOS:
        raise ValueError(f"Tipo de pago inválido. Debe ser uno de: {', '.join(self.TIPOS_PAGO_VALIDOS)}")
    return tipo_pago

@validates('moneda')
def validate_moneda(self, key, moneda):
    if moneda not in self.MONEDAS_VALIDAS:
        raise ValueError(f"Moneda inválida. Debe ser una de: {', '.join(self.MONEDAS_VALIDAS)}")
    return moneda

@validates('cliente_id')
def validate_cliente(self, key, cliente_id):
    if getattr(self, 'tipo', None) == 'credito' and not cliente_id:
        raise ValueError("Cliente es obligatorio para facturas a crédito")
    return cliente_id

@validates('tienda_id')
def validate_tienda(self, key, tienda_id):
    if not tienda_id:
        raise ValueError("Debe seleccionar una tienda")
    return tienda_id

@validates('vendedor_id')
def validate_vendedor(self, key, vendedor_id):
    if not vendedor_id:
        raise ValueError("Debe seleccionar un vendedor")
    return vendedor_id

def to_dict(self):
    """Convierte la factura a un diccionario"""
    return {
        'id': self.id,
        'numero': self.numero,
        'cliente_id': self.cliente_id,
        'cliente_nombre': self.cliente.nombre if self.cliente else None,
        'cliente_ruc': self.cliente.ruc if self.cliente else None,
        'fecha': self.fecha.isoformat() if self.fecha else None,
        'total': float(self.total) if self.total else 0,
        'estatus': self.estatus,
        'tipo': self.tipo,
        'tipo_pago': self.tipo_pago,
        'moneda': self.moneda,
        'tienda_id': self.tienda_id,
        'tienda_nombre': self.tienda.nombre if self.tienda else None,
        'vendedor_id': self.vendedor_id,
        'vendedor_nombre': self.vendedor.nombre if self.vendedor else None,
        'descuento_monto': float(self.descuento_monto) if self.descuento_monto else 0,
        'descuento_porcentaje': float(self.descuento_porcentaje) if self.descuento_porcentaje else 0,
        'notas': self.notas,
        'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        'items': [item.to_dict() for item in self.items] if self.items else []
    }

def __repr__(self):
    return f'<Factura {self.numero} ({self.estatus})>'
    
    
# facturas_models.py
# facturas/facturas_models.py

class TiendaFactura(db.Model):
    __tablename__ = 'tiendafactura'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    moneda = db.Column(db.String(3), default='DOP')
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # Relación actualizada para coincidir con Facturacion
    facturas = db.relationship(
        'Facturacion',
        back_populates='tienda',
        lazy=True
    )

    def __repr__(self):
        return f'<TiendaFactura {self.codigo}: {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'moneda': self.moneda,
            'activa': self.activa,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        } 

# En facturas_models.py
class FacturaTemplate(db.Model):
    __tablename__ = 'factura_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    html_template = db.Column(db.Text, nullable=False)
    css_styles = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    tienda_id = db.Column(db.Integer, db.ForeignKey('tiendafactura.id'))
    
    tienda = db.relationship('TiendaFactura', backref='templates')

class PreFactura(db.Model):
    __tablename__ = 'pre_facturas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estatus = db.Column(db.String(20), default='borrador')
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    cliente = db.relationship('Cliente', backref=db.backref('pre_facturas', lazy=True))
    items = db.relationship('ItemPreFactura', back_populates='pre_factura', lazy=True)

    @validates('numero')
    def validate_unique_numero(self, key, value):
        existing = PreFactura.query.filter(PreFactura.numero == value, PreFactura.id != self.id).first()
        if existing:
            raise IntegrityError("Número de pre-factura ya existe", value, '')
        return value

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente.nombre,
            'fecha': self.fecha.isoformat(),
            'total': self.total,
            'estatus': self.estatus,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<PreFactura {self.numero}>'

class NotaCredito(db.Model):
    __tablename__ = 'notas_credito'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'factura_id': self.factura_id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            
            'motivo': self.motivo
        }

    def __repr__(self):
        return f'<NotaCredito {self.numero}>'

class NotaDebito(db.Model):
    __tablename__ = 'notas_debito'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'factura_id': self.factura_id,
            'monto': self.monto,
            'fecha': self.fecha.isoformat(),
            'motivo': self.motivo
        }

    def __repr__(self):
        return f'<NotaDebito {self.numero}>'

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ruc = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'telefono': self.telefono,
            'email': self.email
        }
        
class Vendedor(db.Model):
    __tablename__ = 'vendedores'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # Definir la relación aquí con backref
    facturas = db.relationship(
        'Facturacion',
        backref='factura_vendedor',
        lazy=True,
        primaryjoin="Vendedor.id == Facturacion.vendedor_id"
    )

    @validates('codigo')
    def validate_codigo(self, key, codigo):
        if not codigo:
            raise ValueError('El código del vendedor es obligatorio')
        return codigo

    @validates('nombre')
    def validate_nombre(self, key, nombre):
        if not nombre:
            raise ValueError('El nombre del vendedor es obligatorio')
        return nombre

    def __repr__(self):
        return f'<Vendedor {self.codigo}: {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'email': self.email,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }     
        
class InvoiceLayoutProcessor:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}",
            "Content-Type": "application/json"
        }

    def generate_layout(self, tienda_id):
        try:
            # Primero desactivar todas las plantillas existentes para esta tienda
            FacturaTemplate.query.filter_by(
                tienda_id=tienda_id
            ).update({'activo': False})
            
            # Generar nueva plantilla
            prompts = [
                "Create a modern professional invoice layout with sleek design",
                "Generate a minimalist business invoice template with elegant typography",
                "Design a corporate invoice layout with modern color scheme"
            ]
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": random.choice(prompts)}
            )

            if response.status_code == 200:
                image_bytes = response.content
                processed_image = base64.b64encode(image_bytes).decode('utf-8')
                
                template = FacturaTemplate(
                    nombre=f"AI_Template_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    html_template=self._generate_random_template(),
                    css_styles=f"data:image/jpeg;base64,{processed_image}",
                    tienda_id=tienda_id,
                    activo=True  # Nueva plantilla activa por defecto
                )
                return template

            raise ValueError(f"Error generando diseño: {response.text}")

        except Exception as e:
            raise ValueError(f"Error generando plantilla: {str(e)}")

    def _generate_random_template(self):
        # Generate random color scheme
        colors = {
            'primary': f'#{random.randint(0, 0xFFFFFF):06x}',
            'secondary': f'#{random.randint(0, 0xFFFFFF):06x}',
            'text': '#333333',
            'border': '#dddddd'
        }
        
        # Generate random layout variations
        layouts = [
            self._modern_layout,
            self._minimal_layout,
            self._corporate_layout,
            self._elegant_layout,
            self._bold_layout
        ]
        
        return random.choice(layouts)(colors)

    # Los layouts existentes...
    def _modern_layout(self, colors):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { 
                    font-family: 'Helvetica Neue', sans-serif; 
                    margin: 0;
                    padding: 40px;
                    color: """ + colors['text'] + """;
                    background: linear-gradient(135deg, """ + colors['primary'] + """10, """ + colors['secondary'] + """10);
                }
                .invoice-container {
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }
                /* ... resto de estilos ... */
            </style>
        </head>
        <body>
            <div class="invoice-container">
                <div class="header">
                    <div class="company-info">
                        <h2>{{ factura.tienda.nombre if factura.tienda else 'N/A' }}</h2>
                        <p>{{ factura.tienda.direccion if factura.tienda else 'N/A' }}</p>
                    </div>
                    <div class="invoice-details">
                        <h2>FACTURA</h2>
                        <p>Número: {{ factura.numero }}</p>
                        <p>Fecha: {{ factura.fecha.strftime('%d/%m/%Y') }}</p>
                    </div>
                </div>

                <div class="client-info">
                    <h3>Cliente</h3>
                    <p>{{ factura.cliente.nombre if factura.cliente else 'N/A' }}</p>
                    <p>RNC/Cédula: {{ factura.cliente.ruc if factura.cliente else 'N/A' }}</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Descripción</th>
                            <th>Cantidad</th>
                            <th>Precio</th>
                            <th>ITBIS</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in factura.items %}
                        {% set itbis_monto = (item.precio_unitario * item.cantidad * item.itbis / 100) if item.itbis else 0 %}
                        <tr>
                            <td>{{ item.item.nombre if item.item else 'N/A' }}</td>
                            <td>{{ item.cantidad }}</td>
                            <td>{{ format_currency(item.precio_unitario) }}</td>
                            <td>{{ format_currency(itbis_monto) }}</td>
                            <td>{{ format_currency(item.cantidad * item.precio_unitario + itbis_monto) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <div class="totals">
                    {% set total_subtotal = 0 %}
                    {% set total_itbis = 0 %}
                    {% for item in factura.items %}
                        {% set subtotal = item.cantidad * item.precio_unitario %}
                        {% set itbis_monto = (subtotal * item.itbis / 100) if item.itbis else 0 %}
                        {% set total_subtotal = total_subtotal + subtotal %}
                        {% set total_itbis = total_itbis + itbis_monto %}
                    {% endfor %}
                    
                    <div>Subtotal: {{ format_currency(total_subtotal) }}</div>
                    <div>ITBIS: {{ format_currency(total_itbis) }}</div>
                    <div>Descuento: {{ format_currency(factura.descuento_monto if factura.descuento_monto else 0) }}</div>
                    <div><strong>Total: {{ format_currency(factura.total) }}</strong></div>
                </div>
            </div>
        </body>
        </html>
        """

    def _minimal_layout(self, colors):
        # Implementar diseño minimalista similar al modern_layout
        return self._modern_layout(colors)  # Por ahora usamos el mismo

    def _corporate_layout(self, colors):
        # Implementar diseño corporativo similar al modern_layout
        return self._modern_layout(colors)  # Por ahora usamos el mismo

    def _elegant_layout(self, colors):
        # Implementar diseño elegante similar al modern_layout
        return self._modern_layout(colors)  # Por ahora usamos el mismo

    def _bold_layout(self, colors):
        # Implementar diseño bold similar al modern_layout
        return self._modern_layout(colors)  # Por ahora usamos el mismo

# Agregar método a la clase FacturaTemplate
def process_layout(self, image_data):
    """Procesa una imagen y actualiza el template usando LayoutLLaVA"""
    processor = InvoiceLayoutProcessor()
    try:
        new_template = processor.analyze_layout(image_data, self.tienda_id)
        self.html_template = new_template.html_template
        self.css_styles = new_template.css_styles
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"Error procesando layout: {str(e)}")
        db.session.rollback()
        raise          
        
class ItemPendiente(db.Model):
    __tablename__ = 'items_pendientes'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items_inventario.id'), nullable=False)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturacion.id'), nullable=True)
    cantidad_pendiente = db.Column(db.Integer, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pendiente')
    override_code = db.Column(db.String(50), nullable=True)

    item = db.relationship('InventarioItem', backref='items_pendientes')
    factura = db.relationship('Facturacion', backref='items_pendientes')     
    
class CodigoAutorizacion(db.Model):
    __tablename__ = 'codigos_autorizacion'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(20), default='stock_override')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, onupdate=datetime.utcnow)
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    activo = db.Column(db.Boolean, default=True)

    creador = db.relationship('Usuario', backref='codigos_autorizacion')

    def __repr__(self):
        return f'<CodigoAutorizacion {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'creado_por': self.creado_por,
            'activo': self.activo
        }