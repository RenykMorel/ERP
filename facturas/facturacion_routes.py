from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from .facturas_models import Facturacion, PreFactura, NotaCredito, NotaDebito, Cliente, ItemPreFactura
from inventario.inventario_models import InventarioItem, MovimientoInventario, ItemFactura
from extensions import db
from . import facturacion_bp
from sqlalchemy.exc import IntegrityError
from datetime import datetime

@facturacion_bp.route('/')
@facturacion_bp.route('/facturas')
@login_required
def facturas():
    facturas = Facturacion.query.all()
    return render_template('facturacion/facturacion_index.html', facturas=facturas)

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/pre-facturas')
def pre_facturas():
    return render_template('pre_facturas.html')

@app.route('/api/pre-facturas', methods=['GET'])
def get_pre_facturas():
    # Here you would typically query your database
    # For now, we'll return dummy data
    pre_facturas = [
        {"id": 1, "numero": "PF001", "cliente": "Cliente A", "fecha": "2023-05-01", "total": 1000, "estatus": "pendiente"},
        {"id": 2, "numero": "PF002", "cliente": "Cliente B", "fecha": "2023-05-02", "total": 1500, "estatus": "aprobada"}
    ]
    return jsonify(pre_facturas)

@app.route('/api/pre-facturas', methods=['POST'])
def create_pre_factura():
    # Here you would typically save the new pre-factura to your database
    # For now, we'll just return a success message
    return jsonify({"message": "Pre-factura creada exitosamente"}), 201

@app.route('/api/pre-facturas/<int:id>', methods=['PUT'])
def update_pre_factura(id):
    # Here you would typically update the pre-factura in your database
    # For now, we'll just return a success message
    return jsonify({"message": f"Pre-factura {id} actualizada exitosamente"})

@app.route('/api/pre-facturas/<int:id>', methods=['DELETE'])
def delete_pre_factura(id):
    # Here you would typically delete the pre-factura from your database
    # For now, we'll just return a success message
    return jsonify({"message": f"Pre-factura {id} eliminada exitosamente"})

if __name__ == '__main__':
    app.run(debug=True)

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

@facturacion_bp.route('/crear-factura', methods=['POST'])
@login_required
def crear_factura():
    data = request.json
    items = data.get('items', [])

    # Verificar stock disponible
    for item_data in items:
        item = InventarioItem.query.get(item_data['id'])
        if item.tipo == 'producto':
            if item.stock < item_data['cantidad']:
                return jsonify({
                    'success': False,
                    'message': f'Stock insuficiente para el producto {item.nombre}. Stock disponible: {item.stock}'
                }), 400

    # Crear la factura
    nueva_factura = Facturacion(
        numero=data['numero'],
        cliente_id=data['cliente_id'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d'),
        total=data['total'],
        usuario_id=current_user.id
    )
    db.session.add(nueva_factura)

    # Procesar los items y actualizar el inventario
    for item_data in items:
        item = InventarioItem.query.get(item_data['id'])
        if item.tipo == 'producto':
            item.stock -= item_data['cantidad']
            
            # Registrar el movimiento de inventario
            movimiento = MovimientoInventario(
                item_id=item.id,
                tipo='salida',
                cantidad=item_data['cantidad'],
                factura_id=nueva_factura.id
            )
            db.session.add(movimiento)

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Factura creada correctamente',
            'factura_id': nueva_factura.id
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error de integridad al crear la factura: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al crear factura: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al crear la factura'
        }), 500

@facturacion_bp.route('/editar-factura/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_factura(id):
    factura = Facturacion.query.get_or_404(id)
    
    if request.method == 'GET':
        return jsonify(factura.to_dict())
    
    data = request.json
    items_nuevos = data.get('items', [])
    
    # Revertir los cambios en el inventario de los items originales
    for item_factura in factura.items:
        if item_factura.item.tipo == 'producto':
            item_factura.item.stock += item_factura.cantidad
    
    # Verificar stock disponible para los nuevos items
    for item_data in items_nuevos:
        item = InventarioItem.query.get(item_data['id'])
        if item.tipo == 'producto':
            if item.stock < item_data['cantidad']:
                return jsonify({
                    'success': False,
                    'message': f'Stock insuficiente para el producto {item.nombre}. Stock disponible: {item.stock}'
                }), 400
    
    # Actualizar la factura
    factura.numero = data['numero']
    factura.cliente_id = data['cliente_id']
    factura.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d')
    factura.total = data['total']
    
    # Eliminar los items antiguos y agregar los nuevos
    factura.items = []
    for item_data in items_nuevos:
        item = InventarioItem.query.get(item_data['id'])
        if item.tipo == 'producto':
            item.stock -= item_data['cantidad']
        
        factura.items.append(item_data)
        
        # Registrar el movimiento de inventario
        if item.tipo == 'producto':
            movimiento = MovimientoInventario(
                item_id=item.id,
                tipo='salida',
                cantidad=item_data['cantidad'],
                factura_id=factura.id
            )
            db.session.add(movimiento)
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Factura actualizada correctamente'
        })
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error de integridad al actualizar la factura: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al actualizar factura: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al actualizar la factura'
        }), 500

@facturacion_bp.route('/eliminar-factura/<int:id>', methods=['POST'])
@login_required
def eliminar_factura(id):
    factura = Facturacion.query.get_or_404(id)
    
    # Revertir los cambios en el inventario
    for item_factura in factura.items:
        if item_factura.item.tipo == 'producto':
            item_factura.item.stock += item_factura.cantidad
    
    try:
        db.session.delete(factura)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Factura eliminada correctamente'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al eliminar factura: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al eliminar la factura'
        }), 500

@facturacion_bp.route('/crear-nota-credito', methods=['POST'])
@login_required
def crear_nota_credito():
    data = request.json
    
    nota_credito = NotaCredito(
        numero=data['numero'],
        factura_id=data['factura_id'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d'),
        monto=data['monto'],
        motivo=data['motivo']
    )
    
    db.session.add(nota_credito)
    
    # Actualizar el inventario si es necesario
    factura = Facturacion.query.get(data['factura_id'])
    for item_factura in factura.items:
        if item_factura.item.tipo == 'producto':
            item_factura.item.stock += item_factura.cantidad
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Nota de crédito creada correctamente'
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al crear nota de crédito: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al crear la nota de crédito'
        }), 500

@facturacion_bp.route('/crear-nota-debito', methods=['POST'])
@login_required
def crear_nota_debito():
    data = request.json
    
    nota_debito = NotaDebito(
        numero=data['numero'],
        factura_id=data['factura_id'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d'),
        monto=data['monto'],
        motivo=data['motivo']
    )
    
    db.session.add(nota_debito)
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Nota de débito creada correctamente'
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al crear nota de débito: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al crear la nota de débito'
        }), 500

@facturacion_bp.route('/crear-cliente', methods=['POST'])
@login_required
def crear_cliente():
    data = request.json
    
    nuevo_cliente = Cliente(
        nombre=data['nombre'],
        ruc=data['ruc'],
        direccion=data.get('direccion'),
        telefono=data.get('telefono'),
        email=data.get('email')
    )
    
    db.session.add(nuevo_cliente)
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Cliente creado correctamente',
            'cliente_id': nuevo_cliente.id
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Ya existe un cliente con ese RUC'
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al crear cliente: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al crear el cliente'
        }), 500

# Puedes agregar más rutas según sea necesario