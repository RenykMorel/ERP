#facturacion_routes.py en la carpeta de facturacion

from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from .facturas_models import (
    Facturacion, PreFactura, NotaCredito, NotaDebito, 
    Cliente, TiendaFactura, ItemPreFactura, Vendedor
)
from common.models import (
    ItemFactura, ItemPreFactura, MovimientoInventario
)
from inventario.inventario_models import InventarioItem
from extensions import db
from . import facturacion_bp
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy import text, func
from .facturas_models import ItemPendiente, CodigoAutorizacion



@facturacion_bp.route('/')
@facturacion_bp.route('/facturas')
@login_required
def facturas():
    facturas = Facturacion.query.all()
    return render_template('facturacion/facturas.html', facturas=facturas)

@facturacion_bp.route('/api/facturas', methods=['GET'])
@login_required
def listar_facturas():
    try:
        print("Iniciando consulta de facturas") # Log 1
        facturas = Facturacion.query.order_by(Facturacion.fecha.desc()).all()
        print(f"Número de facturas encontradas: {len(facturas)}") # Log 2
        
        resultado = []
        for factura in facturas:
            try:
                print(f"Procesando factura ID: {factura.id}") # Log 3
                factura_dict = {
                    'id': factura.id,
                    'numero': factura.numero,
                    'cliente_nombre': factura.cliente.nombre if factura.cliente else 'N/A',
                    'fecha': factura.fecha.strftime('%Y-%m-%d') if factura.fecha else None,
                    'total': float(factura.total or 0),
                    'estatus': factura.estatus or 'pendiente'
                }
                resultado.append(factura_dict)
                print(f"Factura {factura.id} procesada exitosamente") # Log 4
            except Exception as e:
                print(f"Error procesando factura {factura.id}: {str(e)}") # Log 5
                continue
        
        print(f"Resultado final: {resultado}") # Log 6
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Error general en listar_facturas: {str(e)}") # Log 7
        return jsonify({'error': f"Error al cargar las facturas: {str(e)}"}), 500

@facturacion_bp.route('/api/facturas/<int:factura_id>', methods=['GET'])
@login_required
def obtener_factura(factura_id):
    try:
        factura = Facturacion.query.get_or_404(factura_id)
        return jsonify({
            'id': factura.id,
            'numero': factura.numero,
            'cliente_nombre': factura.cliente.nombre if factura.cliente else 'N/A',
            'fecha': factura.fecha.strftime('%Y-%m-%d'),
            'tienda_nombre': factura.tienda.nombre if factura.tienda else 'N/A',
            'estatus': factura.estatus,
            'tipo_pago': factura.tipo_pago,
            'monto': float(factura.total) if factura.total else 0,
            'descuento': float(factura.descuento_monto) if factura.descuento_monto else 0,
            'total': float(factura.total) if factura.total else 0,
            'items': [{
                'producto_nombre': item.item.nombre if item.item else 'N/A',
                'cantidad': item.cantidad,
                'precio_unitario': float(item.precio_unitario) if item.precio_unitario else 0,
                'itbis': float(item.itbis) if item.itbis else 0,
                'subtotal': float(item.cantidad * item.precio_unitario) if item.precio_unitario else 0
            } for item in factura.items]
        })
    except Exception as e:
        current_app.logger.error(f"Error obteniendo factura {factura_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/vendedores', methods=['GET'])
@login_required
def get_vendedores():
    try:
        vendedores = Vendedor.query.order_by(Vendedor.nombre).all()
        return jsonify([vendedor.to_dict() for vendedor in vendedores])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/vendedores', methods=['POST'])
@login_required
def crear_vendedor():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        if not data.get('nombre') or not data.get('codigo'):
            return jsonify({"error": "Nombre y código son requeridos"}), 400
            
        nuevo_vendedor = Vendedor(
            nombre=data['nombre'],
            codigo=data['codigo'],
            telefono=data.get('telefono'),
            email=data.get('email'),
            activo=data.get('activo', True)
        )
        
        db.session.add(nuevo_vendedor)
        db.session.commit()
        
        return jsonify(nuevo_vendedor.to_dict()), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un vendedor con ese código"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/vendedores/<int:id>', methods=['PUT'])
@login_required
def actualizar_vendedor(id):
    try:
        vendedor = Vendedor.query.get_or_404(id)
        data = request.get_json()
        
        if 'nombre' in data:
            vendedor.nombre = data['nombre']
        if 'codigo' in data:
            vendedor.codigo = data['codigo']
        if 'telefono' in data:
            vendedor.telefono = data['telefono']
        if 'email' in data:
            vendedor.email = data['email']
        if 'activo' in data:
            vendedor.activo = data['activo']
        
        db.session.commit()
        return jsonify(vendedor.to_dict())
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un vendedor con ese código"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/vendedores/<int:id>', methods=['DELETE'])
@login_required
def eliminar_vendedor(id):
    try:
        vendedor = Vendedor.query.get_or_404(id)
        db.session.delete(vendedor)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/vendedores/buscar', methods=['GET'])
@login_required
def buscar_vendedores():
    query = request.args.get('q', '')
    try:
        vendedores = Vendedor.query.filter(
            or_(
                Vendedor.nombre.ilike(f'%{query}%'),
                Vendedor.codigo.ilike(f'%{query}%')
            )
        ).all()
        
        return jsonify([vendedor.to_dict() for vendedor in vendedores])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/vendedores/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_vendedor_status(id):
    try:
        vendedor = Vendedor.query.get_or_404(id)
        vendedor.activo = not vendedor.activo
        db.session.commit()
        return jsonify({"message": "Estado del vendedor actualizado", "activo": vendedor.activo})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500    


def obtener_vendedor_principal():
    """Obtiene el vendedor principal. Si no existe, lo crea"""
    vendedor = Vendedor.query.filter_by(codigo='V001').first()
    if not vendedor:
        try:
            vendedor = Vendedor(
                codigo='V001',
                nombre='Vendedor Principal',
                activo=True,
                telefono='000-000-0000',
                email='vendedor.principal@empresa.com'
            )
            db.session.add(vendedor)
            db.session.commit()
            print(f"Vendedor principal creado con ID: {vendedor.id}")
        except Exception as e:
            print(f"Error creando vendedor principal: {str(e)}")
            db.session.rollback()
            return None
    return vendedor

@facturacion_bp.route('/api/vendedores/estado/<int:id>', methods=['PUT'])
@login_required
def cambiar_estado_vendedor(id):
    try:
        vendedor = Vendedor.query.get_or_404(id)
        if vendedor.codigo == 'V001':
            return jsonify({"error": "No se puede modificar el estado del vendedor principal"}), 400
            
        vendedor.activo = not vendedor.activo
        db.session.commit()
        return jsonify({"message": "Estado actualizado", "activo": vendedor.activo})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/config/override-code', methods=['POST'])
@login_required
def set_override_code():
    try:
        # Verificar si es admin
        if not current_user.rol == 'admin':
            return jsonify({"error": "Solo el administrador puede configurar este código"}), 403
            
        data = request.get_json()
        if not data or not data.get('code'):
            return jsonify({"error": "Código requerido"}), 400
        
        # Desactivar códigos anteriores
        CodigoAutorizacion.query.filter_by(
            tipo='stock_override',
            activo=True
        ).update({'activo': False})
        
        # Crear nuevo código de autorización
        nuevo_codigo = CodigoAutorizacion(
            codigo=data['code'],
            tipo='stock_override',
            creado_por=current_user.id,
            activo=True
        )
        
        db.session.add(nuevo_codigo)
        db.session.commit()
        
        return jsonify({"message": "Código configurado exitosamente"})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error configurando código: {str(e)}")
        return jsonify({"error": f"Error al configurar código: {str(e)}"}), 500

@facturacion_bp.route('/api/config/override-code/verify', methods=['POST'])
@login_required
def verify_override_code():
    try:
        data = request.get_json()
        if not data or not data.get('code'):
            return jsonify({"error": "Código requerido"}), 400
            
        # Buscar código activo
        codigo_activo = CodigoAutorizacion.query.filter_by(
            tipo='stock_override',
            activo=True
        ).first()
        
        if not codigo_activo:
            return jsonify({"error": "No hay código de autorización configurado"}), 404
            
        # Verificar código
        if codigo_activo.codigo == data['code']:
            return jsonify({"valid": True, "message": "Código válido"})
        else:
            return jsonify({"valid": False, "message": "Código inválido"}), 401
            
    except Exception as e:
        print(f"Error verificando código: {str(e)}")
        return jsonify({"error": f"Error al verificar código: {str(e)}"}), 500    

@facturacion_bp.route('/api/vendedores/default', methods=['GET'])
@login_required
def get_vendedor_principal():
    try:
        vendedor = obtener_vendedor_principal()
        if not vendedor:
            vendedor = Vendedor(
                codigo='V001',
                nombre='Vendedor Principal',
                activo=True,
                telefono='000-000-0000',
                email='vendedor.principal@empresa.com'
            )
            db.session.add(vendedor)
            db.session.commit()
            print("Vendedor principal creado")
        return jsonify(vendedor.to_dict() if vendedor else {})
    except Exception as e:
        print(f"Error obteniendo vendedor principal: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/facturas', methods=['POST'])
@login_required
def crear_factura():
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Datos inválidos"}), 400
        
        # Validar campos obligatorios (sin vendedor_id)
        required_fields = ['tipo', 'tipo_pago', 'moneda', 'tienda_id', 'items']
        if not all(key in data for key in required_fields):
            return jsonify({
                "error": f"Faltan datos requeridos. Campos obligatorios: {', '.join(required_fields)}"
            }), 400

        try:
            # Convertir campos numéricos
            tienda_id = int(data['tienda_id'])
            cliente_id = int(data.get('cliente_id')) if data.get('cliente_id') else None
            descuento_monto = float(data.get('descuento_monto', 0) or 0)
            descuento_porcentaje = float(data.get('descuento_porcentaje', 0) or 0)
            
            # Manejo del vendedor
            vendedor = None
            if data.get('vendedor_id'):
                try:
                    vendedor_id = int(data['vendedor_id'])
                    vendedor = Vendedor.query.filter_by(id=vendedor_id, activo=True).first()
                    if vendedor:
                        print(f"Usando vendedor seleccionado: {vendedor.nombre}")
                except (ValueError, TypeError):
                    vendedor = None
            
            if not vendedor:
                vendedor = obtener_vendedor_principal()
                if not vendedor:
                    return jsonify({"error": "Error al obtener el vendedor por defecto"}), 500
                print(f"Usando vendedor principal por defecto: {vendedor.nombre}")
            
            # Validar tipo de factura y cliente
            if data['tipo'] not in ['contado', 'credito']:
                return jsonify({"error": "Tipo de factura inválido"}), 400
            
            if data['tipo'] == 'credito' and not cliente_id:
                return jsonify({"error": "El cliente es obligatorio para facturas a crédito"}), 400
            
            # Validar tipo de pago
            if data['tipo_pago'] not in ['efectivo', 'tarjeta', 'transferencia', 'cheque']:
                return jsonify({"error": "Tipo de pago inválido"}), 400
            
            # Validar moneda
            if data['moneda'] not in ['DOP', 'USD']:
                return jsonify({"error": "Moneda inválida"}), 400
            
            # Validar tienda
            tienda = TiendaFactura.query.get(tienda_id)
            if not tienda:
                return jsonify({"error": "Tienda no encontrada"}), 404
            if not tienda.activa:
                return jsonify({"error": "La tienda seleccionada no está activa"}), 400
            if tienda.moneda != data['moneda']:
                return jsonify({"error": f"La moneda debe ser {tienda.moneda}"}), 400
            
            # Validar descuentos
            if descuento_monto < 0:
                return jsonify({"error": "El descuento no puede ser negativo"}), 400
            if descuento_porcentaje < 0 or descuento_porcentaje > 100:
                return jsonify({"error": "Descuento porcentual inválido"}), 400
            
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Error en validación de datos: {str(e)}"}), 400

        # Generar número de factura
        ultimo_numero = Facturacion.query.order_by(Facturacion.numero.desc()).first()
        siguiente_numero = '1'
        if ultimo_numero and ultimo_numero.numero:
            try:
                siguiente_numero = str(int(ultimo_numero.numero.replace('F', '')) + 1)
            except ValueError:
                siguiente_numero = '1'
        nuevo_numero = f"F{siguiente_numero.zfill(8)}"

        # Crear la factura
        nueva_factura = Facturacion(
            numero=nuevo_numero,
            cliente_id=cliente_id,
            fecha=datetime.now().date(),
            tipo=data['tipo'],
            tipo_pago=data['tipo_pago'],
            moneda=data['moneda'],
            tienda_id=tienda_id,
            vendedor_id=vendedor.id,
            descuento_monto=descuento_monto,
            descuento_porcentaje=descuento_porcentaje,
            notas=data.get('notas', ''),
            estatus='pendiente',
            total=0
        )

        # Procesar items
        total = 0
        movimientos_inventario = []
        items_data = data.get('items', [])
        
        if not items_data:
            return jsonify({"error": "La factura debe contener al menos un item"}), 400

        for item_data in items_data:
            try:
                # Validar datos del item
                if not isinstance(item_data, dict):
                    return jsonify({"error": "Formato de item inválido"}), 400
                
                item_id = int(item_data.get('item_id'))
                cantidad = int(item_data.get('cantidad'))
                precio = float(item_data.get('precio_unitario'))
                itbis = float(item_data.get('itbis', 0) or 0)
                
                if cantidad <= 0:
                    return jsonify({"error": "La cantidad debe ser mayor que cero"}), 400
                if precio < 0:
                    return jsonify({"error": "El precio no puede ser negativo"}), 400
                if itbis < 0 or itbis > 100:
                    return jsonify({"error": "ITBIS inválido"}), 400

                # Obtener y validar producto
                producto = db.session.query(InventarioItem).with_for_update().filter_by(id=item_id).first()
                if not producto:
                    return jsonify({"error": f"Producto no encontrado: {item_id}"}), 404

                print(f"Procesando producto: {producto.nombre} (ID: {producto.id})")
                print(f"Stock actual: {producto.stock}")

                # Validar y actualizar inventario
                if producto.tipo == 'producto':
                    stock_actual = producto.stock if producto.stock is not None else 0
                    
                    if stock_actual < cantidad:
                        # Verificar código de override
                        override_code = item_data.get('override_code')
                        codigo_activo = CodigoAutorizacion.query.filter_by(
                            tipo='stock_override',
                            activo=True
                        ).first()
                        
                        if override_code and codigo_activo and codigo_activo.codigo == override_code:
                            print(f"Código de override válido recibido para {producto.nombre}")
                            
                            # Crear item pendiente
                            item_pendiente = ItemPendiente(
                                item_id=producto.id,
                                cantidad_pendiente=cantidad,
                                estado='pendiente',
                                override_code=override_code
                            )
                            db.session.add(item_pendiente)
                            
                            # No actualizar stock aquí, se hará cuando llegue el inventario
                            print(f"Item pendiente creado para {producto.nombre}")
                        else:
                            return jsonify({
                                "error": "stock_insuficiente",
                                "item_id": producto.id,
                                "nombre": producto.nombre,
                                "stock_actual": stock_actual,
                                "cantidad_solicitada": cantidad,
                                "requiere_autorizacion": True,
                                "mensaje": f"Stock insuficiente para {producto.nombre}. Disponible: {stock_actual}"
                            }), 400

                # Crear ítem de factura
                item_factura = ItemFactura(
                    item_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    itbis=itbis,
                    comentario=item_data.get('comentario', ''),
                    override_code=item_data.get('override_code')
                )

                # Calcular totales
                subtotal = cantidad * precio
                itbis_monto = subtotal * (itbis / 100)
                total += subtotal + itbis_monto

                nueva_factura.items.append(item_factura)
                print(f"Item agregado a la factura: {producto.nombre}")

            except Exception as e:
                print(f"Error procesando item: {str(e)}")
                db.session.rollback()
                return jsonify({
                    "error": f"Error procesando item: {str(e)}",
                    "tipo": "error_procesamiento"
                }), 500

        # Aplicar descuentos
        if descuento_porcentaje > 0:
            total = total * (1 - descuento_porcentaje / 100)
        if descuento_monto > 0:
            total = max(0, total - descuento_monto)
        
        nueva_factura.total = round(float(total), 2)

        try:
            # Guardar todo
            db.session.add(nueva_factura)
            for movimiento in movimientos_inventario:
                db.session.add(movimiento)
            
            db.session.commit()
            print(f"Factura creada exitosamente: {nueva_factura.numero}")
            
            return jsonify({
                "success": True,
                "message": "Factura creada exitosamente",
                "factura_id": nueva_factura.id,
                "numero": nueva_factura.numero,
                "total": nueva_factura.total,
                "tienda": tienda.nombre,
                "vendedor": vendedor.nombre,
                "tipo": nueva_factura.tipo,
                "tipo_pago": nueva_factura.tipo_pago,
                "cliente": nueva_factura.cliente.nombre if nueva_factura.cliente else None,
                "fecha": nueva_factura.fecha.strftime('%Y-%m-%d')
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error en commit final: {str(e)}")
            return jsonify({"error": f"Error guardando la factura: {str(e)}"}), 500
            
    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/pre-facturas')
@login_required
def pre_facturas():
    return render_template('facturacion/pre_facturas.html')

@facturacion_bp.route('/api/pre-facturas', methods=['GET'])
@login_required
def get_pre_facturas():
    try:
        pre_facturas = PreFactura.query.order_by(PreFactura.fecha.desc()).all()
        return jsonify([{
            'id': pf.id,
            'numero': pf.numero,
            'cliente': pf.cliente.nombre if pf.cliente else 'N/A',
            'fecha': pf.fecha.strftime('%Y-%m-%d'),
            'total': float(pf.total) if pf.total else 0,
            'estatus': pf.estatus
        } for pf in pre_facturas])
    except Exception as e:
        current_app.logger.error(f"Error listando pre-facturas: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/autorizacion/codigo', methods=['POST'])
@login_required
def configurar_codigo_autorizacion():
    if not current_user.rol == 'admin':
        return jsonify({"error": "Solo el administrador puede configurar este código"}), 403
        
    data = request.get_json()
    if not data or not data.get('codigo'):
        return jsonify({"error": "Código requerido"}), 400
    
    try:
        # Desactivar códigos anteriores
        CodigoAutorizacion.query.filter_by(tipo='stock_override', activo=True).update({'activo': False})
        
        # Crear nuevo código
        nuevo_codigo = CodigoAutorizacion(
            codigo=data['codigo'],
            creado_por=current_user.id
        )
        db.session.add(nuevo_codigo)
        db.session.commit()
        
        return jsonify({"message": "Código de autorización configurado exitosamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/autorizacion/verificar', methods=['POST'])
@login_required
def verificar_codigo():
    data = request.get_json()
    if not data or not data.get('codigo'):
        return jsonify({"error": "Código requerido"}), 400
        
    codigo_activo = CodigoAutorizacion.query.filter_by(
        tipo='stock_override',
        activo=True
    ).first()
    
    if not codigo_activo:
        return jsonify({"error": "No hay código de autorización configurado"}), 404
        
    if codigo_activo.codigo != data['codigo']:
        return jsonify({"error": "Código inválido"}), 401
        
    return jsonify({"valid": True})    

@facturacion_bp.route('/api/pre-facturas', methods=['POST'])
@login_required
def create_pre_factura():
    try:
        data = request.get_json()
        # Implementar la lógica real aquí
        return jsonify({"message": "Pre-factura creada exitosamente"}), 201
    except Exception as e:
        current_app.logger.error(f"Error creando pre-factura: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/pre-facturas/<int:id>', methods=['PUT'])
@login_required
def update_pre_factura(id):
    try:
        # Implementar la lógica real aquí
        return jsonify({"message": f"Pre-factura {id} actualizada exitosamente"})
    except Exception as e:
        current_app.logger.error(f"Error actualizando pre-factura: {str(e)}")
        return jsonify({"error": str(e)}), 500

@facturacion_bp.route('/api/pre-facturas/<int:id>', methods=['DELETE'])
@login_required
def delete_pre_factura(id):
    try:
        # Implementar la lógica real aquí
        return jsonify({"message": f"Pre-factura {id} eliminada exitosamente"})
    except Exception as e:
        current_app.logger.error(f"Error eliminando pre-factura: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
    
    # Validar campos obligatorios
    required_fields = ['tipo', 'tipo_pago', 'moneda', 'tienda_id']
    if not all(key in data for key in required_fields):
        return jsonify({
            "error": f"Faltan datos requeridos. Campos obligatorios: {', '.join(required_fields)}"
        }), 400
    
    # Validar cliente para crédito
    if data['tipo'] == 'credito' and not data.get('cliente_id'):
        return jsonify({"error": "El cliente es obligatorio para facturas a crédito"}), 400
    
    try:
        # Actualizar campos básicos
        for field in ['tipo', 'tipo_pago', 'moneda', 'tienda_id', 'cliente_id']:
            if field in data:
                setattr(factura, field, data[field])
        
        # Eliminar items existentes
        factura.items = []
        
        # Procesar nuevos items
        for item_data in data.get('items', []):
            item_factura = ItemFactura(
                item_id=item_data['item_id'],
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario'],
                itbis=item_data.get('itbis', 0),
                comentario=item_data.get('comentario', '')
            )
            factura.items.append(item_factura)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Factura actualizada correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al actualizar factura: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al actualizar la factura'
        }), 500
        
@facturacion_bp.route('/api/tiendas', methods=['GET', 'POST'])
@login_required
def handle_stores():
    if request.method == 'GET':
        try:
            tiendas = TiendaFactura.query.all()
            return jsonify([tienda.to_dict() for tienda in tiendas]), 200
        except Exception as e:
            current_app.logger.error(f"Error obteniendo tiendas: {str(e)}")
            return jsonify({"error": "Error al obtener las tiendas"}), 500

    elif request.method == 'POST':
        try:
            data = request.get_json()

            # Validación básica
            if not data.get('codigo') or not data.get('nombre'):
                return jsonify({'error': 'El código y el nombre son requeridos'}), 400

            # Crear la tienda directamente
            new_store = TiendaFactura(
                codigo=data['codigo'],
                nombre=data['nombre'],
                direccion=data.get('direccion'),
                telefono=data.get('telefono'),
                email=data.get('email'),
                moneda=data.get('moneda', 'DOP'),
                activa=data.get('activa', True)
            )
            db.session.add(new_store)
            db.session.commit()
            return jsonify(new_store.to_dict()), 201

        except IntegrityError as e:
            # Manejar duplicados con rollback
            db.session.rollback()
            current_app.logger.error(f"Error de integridad: {str(e)}")
            return jsonify({
                'error': f'Ya existe una tienda con el código {data.get("codigo")}'
            }), 409

        except Exception as e:
            # Manejo de otros errores con rollback
            db.session.rollback()
            current_app.logger.error(f"Error creando tienda: {str(e)}")
            return jsonify({'error': 'Error interno al crear la tienda'}), 500

@facturacion_bp.route('/api/tiendas/<int:tienda_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def handle_store(tienda_id):
    tienda = TiendaFactura.query.get_or_404(tienda_id)
    
    if request.method == 'GET':
        return jsonify(tienda.to_dict())
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if not data.get('codigo') or not data.get('nombre'):
                return jsonify({'error': 'Código y nombre son requeridos'}), 400
                
            existing_store = TiendaFactura.query.filter_by(codigo=data['codigo']).first()
            if existing_store and existing_store.id != tienda_id:
                return jsonify({'error': 'Ya existe otra tienda con este código'}), 400
            
            for key, value in data.items():
                if hasattr(tienda, key):
                    setattr(tienda, key, value)
            
            db.session.commit()
            
            return jsonify(tienda.to_dict())
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error actualizando tienda: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'DELETE':
        try:
            db.session.delete(tienda)
            db.session.commit()
            return '', 204
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error eliminando tienda: {str(e)}")
            return jsonify({'error': str(e)}), 500
     
        
@facturacion_bp.route('/api/tiendas', methods=['GET'])
@login_required
def get_tiendas():
    try:
        tiendas = TiendaFactura.query.filter_by(activa=True).order_by(TiendaFactura.nombre).all()
        return jsonify([{
            'id': tienda.id,
            'codigo': tienda.codigo,
            'nombre': tienda.nombre,
            'direccion': tienda.direccion,
            'telefono': tienda.telefono,
            'email': tienda.email,
            'moneda': tienda.moneda,
            'activa': tienda.activa,
            'fecha_creacion': tienda.fecha_creacion.isoformat() if tienda.fecha_creacion else None,
            'fecha_actualizacion': tienda.fecha_actualizacion.isoformat() if tienda.fecha_actualizacion else None
        } for tienda in tiendas])
    except Exception as e:
        current_app.logger.error(f"Error obteniendo tiendas: {str(e)}")
        return jsonify({"error": str(e)}), 500      

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


