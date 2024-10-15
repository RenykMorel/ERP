from flask import Blueprint, jsonify, request, render_template
from facturacion_models import Factura, DetalleFactura, Cliente, Producto
from extensions import db

facturacion = Blueprint('facturacion', __name__)

# ... resto del código ...

import logging

@facturacion.route('/facturas', methods=['GET'])
def obtener_facturas():
    logging.info('Solicitud recibida para obtener facturas')
    facturas = Factura.query.all()
    logging.info(f'Número de facturas recuperadas: {len(facturas)}')
    return jsonify([{
        'numero': factura.numero,
        'total': factura.total,
    } for factura in facturas])

@facturacion.route('/facturas', methods=['POST'])
def crear_factura():
    data = request.json
    nueva_factura = Factura(
        numero=data['numero'],
        cliente_id=data['cliente_id'],
        total=data['total']
    )
    db.session.add(nueva_factura)
    db.session.commit()
    return jsonify(nueva_factura.to_dict()), 201

# Agregar más rutas para CRUD de facturas, clientes y productos