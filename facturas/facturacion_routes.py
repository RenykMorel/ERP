from flask import render_template, request, jsonify, current_app
from flask_login import login_required
from .facturas_models import Facturacion, PreFactura, NotaCredito, NotaDebito, Cliente
from extensions import db
from . import facturacion_bp

@facturacion_bp.route('/')
@facturacion_bp.route('/facturas')
@login_required
def facturas():
    facturas = Facturacion.query.all()
    return render_template('facturacion/facturacion_index.html', facturas=facturas)

@facturacion_bp.route('/pre-facturas')
@login_required
def pre_facturas():
    pre_facturas = PreFactura.query.all()
    return render_template('facturacion/pre_facturas.html', pre_facturas=pre_facturas)

@facturacion_bp.route('/notas-credito-debito')
@login_required
def notas_credito_debito():
    notas_credito = NotaCredito.query.all()
    notas_debito = NotaDebito.query.all()
    return render_template('facturacion/notas_de_credito_debito.html', notas_credito=notas_credito, notas_debito=notas_debito)

@facturacion_bp.route('/reporte-ventas')
@login_required
def reporte_ventas():
    # Aquí irá la lógica para generar el reporte de ventas
    return render_template('facturacion/reporte_de_ventas.html')

@facturacion_bp.route('/gestion-clientes')
@login_required
def gestion_clientes():
    clientes = Cliente.query.all()
    return render_template('facturacion/gestion_de_clientes.html', clientes=clientes)

# Aquí puedes agregar más rutas según sea necesario, como crear, editar o eliminar facturas

@facturacion_bp.route('/crear-factura', methods=['POST'])
@login_required
def crear_factura():
    # Lógica para crear una nueva factura
    pass

@facturacion_bp.route('/editar-factura/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_factura(id):
    # Lógica para editar una factura existente
    pass

@facturacion_bp.route('/eliminar-factura/<int:id>', methods=['POST'])
@login_required
def eliminar_factura(id):
    # Lógica para eliminar una factura
    pass