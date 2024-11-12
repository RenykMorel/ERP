#facturacion_routes.py en la carpeta de facturacion

from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from .facturas_models import Facturacion, PreFactura, NotaCredito, NotaDebito, Cliente, ItemPreFactura
from inventario.inventario_models import InventarioItem, MovimientoInventario, ItemFactura
from extensions import db
from . import facturacion_bp
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .facturas_models import Facturacion, PreFactura, NotaCredito, NotaDebito, Cliente
from common.models import ItemFactura, ItemPreFactura, MovimientoInventario
from sqlalchemy import or_


@facturacion_bp.route('/')
@facturacion_bp.route('/facturas')
@login_required
def facturas():
    facturas = Facturacion.query.all()
    return render_template('facturacion/facturas.html', facturas=facturas)

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



# Puedes agregar más rutas según sea necesario

@facturacion_bp.route('/api/clientes', methods=['GET'])
@login_required
def get_clientes():
    try:
        clientes = Cliente.query.order_by(Cliente.nombre).all()
        return jsonify([{
            'id': cliente.id,
            'nombre': cliente.nombre,
            'ruc': cliente.ruc,
            'telefono': cliente.telefono,
            'email': cliente.email
        } for cliente in clientes])
    except Exception as e:
        current_app.logger.error(f"Error obteniendo clientes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/clientes', methods=['POST'])
@login_required
def crear_cliente():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        # Validar datos requeridos
        if not data.get('nombre') or not data.get('ruc'):
            return jsonify({"error": "Nombre y RNC/Cédula son requeridos"}), 400
            
        nuevo_cliente = Cliente(
            nombre=data['nombre'],
            ruc=data['ruc'],
            telefono=data.get('telefono'),
            email=data.get('email')
        )
        
        db.session.add(nuevo_cliente)
        db.session.commit()
        
        return jsonify({
            "id": nuevo_cliente.id,
            "nombre": nuevo_cliente.nombre,
            "ruc": nuevo_cliente.ruc,
            "telefono": nuevo_cliente.telefono,
            "email": nuevo_cliente.email,
            "message": "Cliente creado exitosamente"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al crear cliente: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/clientes/buscar', methods=['GET'])
@login_required
def buscar_clientes():
    query = request.args.get('q', '')
    try:
        clientes = Cliente.query.filter(
            or_(
                Cliente.nombre.ilike(f'%{query}%'),
                Cliente.ruc.ilike(f'%{query}%')
            )
        ).all()
        
        return jsonify([{
            'id': cliente.id,
            'nombre': cliente.nombre,
            'ruc': cliente.ruc,
            'telefono': cliente.telefono,
            'email': cliente.email
        } for cliente in clientes])
    except Exception as e:
        current_app.logger.error(f"Error buscando clientes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/productos/buscar', methods=['GET'])
@login_required
def buscar_productos():
    query = request.args.get('q', '')
    try:
        productos = InventarioItem.query.filter(
            or_(
                InventarioItem.nombre.ilike(f'%{query}%'),
                InventarioItem.codigo.ilike(f'%{query}%')
            )
        ).all()
        return jsonify([{
            'id': producto.id,
            'nombre': producto.nombre,
            'codigo': producto.codigo,
            'stock': producto.stock,
            'precio_venta': float(producto.precio) if producto.precio else 0,
            'itbis': float(producto.itbis) if producto.itbis else 0
        } for producto in productos])
    except Exception as e:
        current_app.logger.error(f"Error buscando productos: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/facturas', methods=['GET'])
@login_required
def listar_facturas():
    try:
        facturas = Facturacion.query.order_by(Facturacion.fecha.desc()).all()
        return jsonify([{
            'id': factura.id,
            'numero': factura.numero,
            'cliente_nombre': factura.cliente.nombre if factura.cliente else 'N/A',
            'fecha': factura.fecha.strftime('%Y-%m-%d'),
            'total': float(factura.total) if factura.total else 0,
            'estatus': factura.estatus
        } for factura in facturas])
    except Exception as e:
        current_app.logger.error(f"Error listando facturas: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/facturas/<int:factura_id>', methods=['GET'])
@login_required
def obtener_factura(factura_id):
    try:
        factura = Facturacion.query.get_or_404(factura_id)
        return jsonify({
            'id': factura.id,
            'numero': factura.numero,
            'cliente': {
                'id': factura.cliente.id,
                'nombre': factura.cliente.nombre,
                'ruc': factura.cliente.ruc
            } if factura.cliente else None,
            'fecha': factura.fecha.strftime('%Y-%m-%d'),
            'total': float(factura.total) if factura.total else 0,
            'estatus': factura.estatus,
            'items': [{
                'id': item.id,
                'producto_id': item.item_id,
                'producto_nombre': item.item.nombre if item.item else 'N/A',
                'cantidad': item.cantidad,
                'precio_unitario': float(item.precio_unitario) if item.precio_unitario else 0,
                'total': float(item.cantidad * item.precio_unitario) if item.precio_unitario else 0
            } for item in factura.items]
        })
    except Exception as e:
        current_app.logger.error(f"Error obteniendo factura {factura_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@facturacion_bp.route('/api/facturas', methods=['POST'])
@login_required
def crear_factura():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not all(key in data for key in ['cliente_id', 'items']):
            return jsonify({"error": "Faltan datos requeridos"}), 400
        
        # Generar número de factura
        ultimo_numero = Facturacion.query.order_by(Facturacion.numero.desc()).first()
        nuevo_numero = f"F{str(int(ultimo_numero.numero[1:]) + 1).zfill(8)}" if ultimo_numero else "F00000001"
        
        # Crear la factura
        nueva_factura = Facturacion(
            numero=nuevo_numero,
            cliente_id=data['cliente_id'],
            fecha=datetime.now(),
            descuento=data.get('descuento', 0),
            notas=data.get('notas', ''),
            tipo=data.get('tipo', 'contado'),
            tipo_pago=data.get('tipo_pago', 'efectivo'),
            usuario_id=current_user.id,
            estatus='pendiente'
        )
        
        total = 0
        
        # Agregar items
        for item_data in data['items']:
            producto = InventarioItem.query.get(item_data['item_id'])
            if not producto:
                return jsonify({"error": f"Producto no encontrado: {item_data['item_id']}"}), 404
                
            # Verificar stock si es producto
            if producto.tipo == 'producto' and producto.stock < item_data['cantidad']:
                return jsonify({
                    "error": f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}"
                }), 400
            
            # Crear item de factura
            item_factura = ItemFactura(
                item_id=producto.id,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario'],
                itbis=item_data.get('itbis', 0),
                comentario=item_data.get('comentario', '')
            )
            
            subtotal = item_data['cantidad'] * item_data['precio_unitario']
            itbis_monto = subtotal * (item_data.get('itbis', 0) / 100)
            total += subtotal + itbis_monto
            
            nueva_factura.items.append(item_factura)
            
            # Actualizar inventario y registrar movimiento si es producto
            if producto.tipo == 'producto':
                producto.stock -= item_data['cantidad']
                
                movimiento = MovimientoInventario(
                    item_id=producto.id,
                    tipo='salida',
                    cantidad=item_data['cantidad'],
                    usuario_id=current_user.id,
                    motivo='Venta - Factura'
                )
                db.session.add(movimiento)
        
        # Aplicar descuento
        if data.get('descuento'):
            descuento = data['descuento']
            if isinstance(descuento, str) and '%' in descuento:
                porcentaje = float(descuento.replace('%', '')) / 100
                total = total * (1 - porcentaje)
            else:
                total -= float(descuento)
        
        nueva_factura.total = total
        
        db.session.add(nueva_factura)
        db.session.commit()
        
        return jsonify({
            "message": "Factura creada exitosamente",
            "factura_id": nueva_factura.id,
            "numero": nueva_factura.numero,
            "total": float(nueva_factura.total)
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Error de integridad creando factura: {str(e)}")
        return jsonify({"error": "Error de integridad en la base de datos"}), 400
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creando factura: {str(e)}")
        return jsonify({"error": str(e)}), 500