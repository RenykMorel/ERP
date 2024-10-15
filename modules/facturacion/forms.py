from flask_wtf import FlaskForm
from wtforms import StringField, DateField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from datetime import date

class FacturaForm(FlaskForm):
    numero = StringField('Número de Factura', validators=[
        DataRequired(),
        Length(min=1, max=20, message='El número de factura debe tener entre 1 y 20 caracteres.')
    ])
    cliente = StringField('Cliente', validators=[
        DataRequired(),
        Length(min=2, max=100, message='El nombre del cliente debe tener entre 2 y 100 caracteres.')
    ])
    fecha = DateField('Fecha', validators=[DataRequired()], default=date.today)
    total = DecimalField('Total', validators=[
        DataRequired(),
        NumberRange(min=0, message='El total debe ser un número positivo.')
    ])
    estatus = SelectField('Estatus', choices=[
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada')
    ], validators=[DataRequired()])
    submit = SubmitField('Guardar Factura')

class BusquedaFacturaForm(FlaskForm):
    numero_factura = StringField('Número de Factura')
    cliente = StringField('Cliente')
    fecha_desde = DateField('Fecha Desde')
    fecha_hasta = DateField('Fecha Hasta')
    estatus = SelectField('Estatus', choices=[
        ('', 'Todos'),
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada')
    ])
    submit = SubmitField('Buscar')

class ItemFacturaForm(FlaskForm):
    descripcion = StringField('Descripción', validators=[
        DataRequired(),
        Length(max=200, message='La descripción no puede exceder los 200 caracteres.')
    ])
    cantidad = DecimalField('Cantidad', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='La cantidad debe ser mayor que cero.')
    ])
    precio_unitario = DecimalField('Precio Unitario', validators=[
        DataRequired(),
        NumberRange(min=0, message='El precio unitario debe ser un número positivo.')
    ])
    submit = SubmitField('Añadir Item')

# Puedes agregar más formularios según sea necesario