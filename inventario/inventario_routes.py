from flask import render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import distinct  
from datetime import datetime
from . import inventario_bp
from .inventario_models import InventarioItem, MovimientoInventario, AjusteInventario, TipoItem, CategoriaItem, Almacen
from extensions import db
import logging
import io  
import csv


logger = logging.getLogger(__name__)



@inventario_bp.route('/')
@login_required
def index():
    return render_template('inventario/index.html')

@inventario_bp.route('/items')
@login_required
def items():
    return render_template('inventario/items.html')

@inventario_bp.route('/api/items', methods=['GET'])
@login_required
def get_items():
    try:
        items = InventarioItem.query.all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        logger.error(f"Error al obtener items: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/items', methods=['POST'])
@login_required
def create_item():
    try:
        if not request.is_json:
            return jsonify({"error": "Se requiere JSON"}), 400
            
        data = request.get_json()
        logger.info(f"Datos recibidos para crear item: {data}")
        
        # Validación del tipo
        tipo = data.get('tipo')
        if not tipo or tipo not in ['producto', 'servicio', 'otro']:
            return jsonify({"error": "El tipo debe ser 'producto', 'servicio' u 'otro'"}), 400

        # Validar y convertir campos numéricos con valores por defecto
        try:
            stock = int(data.get('stock', 0) if data.get('stock') is not None else 0)
            stock_minimo = int(data.get('stock_minimo', 0) if data.get('stock_minimo') is not None else 0)
            stock_maximo = int(data.get('stock_maximo', 0) if data.get('stock_maximo') is not None else 0)
            costo = float(data.get('costo', 0) if data.get('costo') is not None else 0)
            itbis = float(data.get('itbis', 0) if data.get('itbis') is not None else 0)
            margen = float(data.get('margen', 0) if data.get('margen') is not None else 0)
            precio = float(data.get('precio', 0) if data.get('precio') is not None else 0)
        except (ValueError, TypeError) as e:
            return jsonify({
                "error": "Error en la conversión de datos numéricos",
                "detalle": str(e)
            }), 400
        
        # Validar campos requeridos
        required_fields = {
            'nombre': data.get('nombre'),
            'tipo': tipo,
            'costo': costo,
            'itbis': itbis,
            'margen': margen,
            'precio': precio
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value and value != 0]
        if missing_fields:
            return jsonify({
                "error": "Faltan campos requeridos",
                "campos": missing_fields
            }), 400

        # Crear el item con los campos validados
        new_item = InventarioItem(
            codigo=data.get('codigo'),
            nombre=data['nombre'],
            tipo=tipo,
            descripcion=data.get('descripcion'),
            categoria=data.get('categoria'),
            proveedor=data.get('proveedor'),
            marca=data.get('marca'),
            unidad_medida=data.get('unidad_medida'),
            stock=stock,
            stock_minimo=stock_minimo,
            stock_maximo=stock_maximo,
            costo=costo,
            itbis=itbis,
            margen=margen,
            precio=precio,
            tipo_item_id=data.get('tipo_item_id')
        )

        db.session.add(new_item)
        db.session.commit()
        
        logger.info(f"Item creado exitosamente: {new_item.id}")
        return jsonify(new_item.to_dict()), 201
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Error de integridad: {str(e)}")
        return jsonify({
            "error": "Error de integridad en la base de datos",
            "detalle": "Ya existe un item con ese código" if "unique" in str(e).lower() else str(e)
        }), 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear item: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor",
            "detalle": str(e)
        }), 500
@inventario_bp.route('/api/items/<int:item_id>', methods=['GET'])
@login_required
def get_item(item_id):
    try:
        item = InventarioItem.query.get_or_404(item_id)
        item_data = {
            'id': item.id,
            'codigo': item.codigo,
            'nombre': item.nombre,
            'tipo': item.tipo,
            'categoria': item.categoria,
            'descripcion': item.descripcion,
            'proveedor': item.proveedor,
            'marca': item.marca,
            'unidad_medida': item.unidad_medida,
            'stock': item.stock,
            'stock_minimo': item.stock_minimo,
            'stock_maximo': item.stock_maximo,
            'costo': float(item.costo) if item.costo else 0,
            'itbis': float(item.itbis) if item.itbis else 0,
            'margen': float(item.margen) if item.margen else 0,
            'precio': float(item.precio) if item.precio else 0,
            'tipo_item_id': item.tipo_item_id
        }
        logger.info(f"Item recuperado: {item_data}")
        return jsonify(item_data)
    except Exception as e:
        logger.error(f"Error al obtener item {item_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@inventario_bp.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    try:
        item = InventarioItem.query.get_or_404(item_id)
        data = request.get_json()
        
        # Validar y convertir campos numéricos
        try:
            if 'stock' in data:
                data['stock'] = int(data['stock'] if data['stock'] is not None else 0)
            if 'stock_minimo' in data:
                data['stock_minimo'] = int(data['stock_minimo'] if data['stock_minimo'] is not None else 0)
            if 'stock_maximo' in data:
                data['stock_maximo'] = int(data['stock_maximo'] if data['stock_maximo'] is not None else 0)
            if 'costo' in data:
                data['costo'] = float(data['costo'] if data['costo'] is not None else 0)
            if 'itbis' in data:
                data['itbis'] = float(data['itbis'] if data['itbis'] is not None else 0)
            if 'margen' in data:
                data['margen'] = float(data['margen'] if data['margen'] is not None else 0)
            if 'precio' in data:
                data['precio'] = float(data['precio'] if data['precio'] is not None else 0)
        except (ValueError, TypeError) as e:
            return jsonify({
                "error": "Error en la conversión de datos numéricos",
                "detalle": str(e)
            }), 400

        # Actualizar campos del item
        for field in ['nombre', 'tipo', 'categoria', 'descripcion', 'proveedor', 
                     'marca', 'unidad_medida', 'stock', 'stock_minimo', 'stock_maximo',
                     'costo', 'itbis', 'margen', 'precio', 'tipo_item_id']:
            if field in data:
                setattr(item, field, data[field])

        db.session.commit()
        logger.info(f"Item actualizado: {item.id}")
        return jsonify(item.to_dict())
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Error de integridad: {str(e)}")
        return jsonify({"error": "Ya existe un item con ese código"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar item: {str(e)}")
        return jsonify({"error": str(e)}), 500

@inventario_bp.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    item = InventarioItem.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar item: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Rutas para Entrada de Almacén
@inventario_bp.route('/entrada-almacen')
@login_required
def entrada_almacen():
    return render_template('inventario/entrada_almacen.html')

@inventario_bp.route('/api/entrada-almacen', methods=['POST'])
@login_required
def create_entrada_almacen():
    data = request.json
    try:
        for item_data in data['items']:
            item = InventarioItem.query.get_or_404(item_data['item_id'])
            if item.tipo != 'producto':
                return jsonify({"error": f"El item {item.codigo} no es un producto"}), 400
            
            movimiento = MovimientoInventario(
                item_id=item.id,
                tipo='entrada',
                cantidad=item_data['cantidad'],
                fecha=datetime.utcnow(),
                usuario_id=current_user.id
            )
            db.session.add(movimiento)
            item.stock += item_data['cantidad']
        
        db.session.commit()
        return jsonify({"message": "Entrada de almacén registrada correctamente"}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al registrar entrada de almacén: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Rutas para Salida de Almacén
@inventario_bp.route('/salida-almacen')
@login_required
def salida_almacen():
    return render_template('inventario/salida_almacen.html')

@inventario_bp.route('/api/salida-almacen', methods=['POST'])
@login_required
def create_salida_almacen():
    data = request.json
    try:
        for item_data in data['items']:
            item = InventarioItem.query.get_or_404(item_data['item_id'])
            if item.tipo != 'producto':
                return jsonify({"error": f"El item {item.codigo} no es un producto"}), 400
            if item.stock < item_data['cantidad']:
                return jsonify({"error": f"Stock insuficiente para el item {item.codigo}"}), 400
            
            movimiento = MovimientoInventario(
                item_id=item.id,
                tipo='salida',
                cantidad=item_data['cantidad'],
                fecha=datetime.utcnow(),
                usuario_id=current_user.id
            )
            db.session.add(movimiento)
            item.stock -= item_data['cantidad']
        
        db.session.commit()
        return jsonify({"message": "Salida de almacén registrada correctamente"}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al registrar salida de almacén: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para Inventario
@inventario_bp.route('/inventario')
@login_required
def inventario():
    return render_template('inventario/inventario.html')

@inventario_bp.route('/api/inventario')
@login_required
def get_inventario():
    try:
        items = InventarioItem.query.filter_by(tipo='producto').all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        current_app.logger.error(f"Error al obtener inventario: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

# Ruta para Reporte de Inventario
# Ruta para Reporte de Inventario
@inventario_bp.route('/reporte')
@login_required
def reporte():
    return render_template('inventario/reporte.html')

@inventario_bp.route('/api/reporte', methods=['GET'])
@login_required
def get_reporte():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    categoria = request.args.get('categoria')
    
    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Se requieren fechas de inicio y fin"}), 400
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        
        # Obtener los items según la categoría
        items_query = InventarioItem.query
        if categoria:
            items_query = items_query.filter(InventarioItem.categoria == categoria)
        items = items_query.all()

        # Preparar el resumen y detalle
        resumen = {
            "total_items": len(items),
            "valor_total": 0.0,
            "items_stock_bajo": 0
        }

        detalle = []
        
        for item in items:
            # Obtener movimientos en el período
            movimientos = MovimientoInventario.query.filter(
                MovimientoInventario.item_id == item.id,
                MovimientoInventario.fecha.between(fecha_inicio, fecha_fin)
            ).all()

            # Calcular movimientos
            entradas = sum(m.cantidad for m in movimientos if m.tipo == 'entrada')
            salidas = sum(m.cantidad for m in movimientos if m.tipo == 'salida')
            
            # Calcular stock inicial
            movimientos_anteriores = MovimientoInventario.query.filter(
                MovimientoInventario.item_id == item.id,
                MovimientoInventario.fecha < fecha_inicio
            ).all()
            
            total_entradas_previas = sum(m.cantidad for m in movimientos_anteriores if m.tipo == 'entrada')
            total_salidas_previas = sum(m.cantidad for m in movimientos_anteriores if m.tipo == 'salida')
            stock_inicial = item.stock - (total_entradas_previas - total_salidas_previas)
            
            # Calcular valores
            valor_unitario = float(item.costo)
            stock_actual = stock_inicial + entradas - salidas
            valor_total = stock_actual * valor_unitario

            # Agregar al detalle
            detalle.append({
                "codigo": item.codigo or str(item.id),
                "nombre": item.nombre,
                "categoria": item.categoria or "Sin categoría",
                "stock_inicial": stock_inicial,
                "entradas": entradas,
                "salidas": salidas,
                "stock_actual": stock_actual,
                "valor_unitario": valor_unitario,
                "valor_total": valor_total
            })

            # Actualizar resumen
            resumen["valor_total"] += valor_total
            if 1 <= stock_actual <= 5:  # Changed to consider stock between 1 and 5 as low
                resumen["items_stock_bajo"] += 1

        return jsonify({
            "resumen": resumen,
            "detalle": detalle
        })

    except ValueError as e:
        logger.error(f"Error de validación en reporte: {str(e)}")
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    except Exception as e:
        logger.error(f"Error al generar reporte: {str(e)}", exc_info=True)
        return jsonify({"error": "Error interno del servidor"}), 500







@inventario_bp.route('/api/exportar-excel', methods=['GET'])
@login_required
def exportar_excel():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    categoria = request.args.get('categoria')
    
    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Se requieren fechas de inicio y fin"}), 400
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        
        # Obtener los items
        items_query = InventarioItem.query
        if categoria:
            items_query = items_query.filter(InventarioItem.categoria == categoria)
        items = items_query.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow([
            'Código',
            'Nombre',
            'Categoría',
            'Stock Inicial',
            'Entradas',
            'Salidas',
            'Stock Actual',
            'Valor Unitario',
            'Valor Total'
        ])
        
        for item in items:
            # Obtener movimientos
            movimientos = MovimientoInventario.query.filter(
                MovimientoInventario.item_id == item.id,
                MovimientoInventario.fecha.between(fecha_inicio, fecha_fin)
            ).all()

            # Calcular movimientos
            entradas = sum(m.cantidad for m in movimientos if m.tipo == 'entrada')
            salidas = sum(m.cantidad for m in movimientos if m.tipo == 'salida')
            
            # Calcular stock inicial
            movimientos_anteriores = MovimientoInventario.query.filter(
                MovimientoInventario.item_id == item.id,
                MovimientoInventario.fecha < fecha_inicio
            ).all()
            
            total_entradas_previas = sum(m.cantidad for m in movimientos_anteriores if m.tipo == 'entrada')
            total_salidas_previas = sum(m.cantidad for m in movimientos_anteriores if m.tipo == 'salida')
            stock_inicial = item.stock - (total_entradas_previas - total_salidas_previas)
            stock_actual = stock_inicial + entradas - salidas

            writer.writerow([
                item.codigo or str(item.id),
                item.nombre,
                item.categoria or "Sin categoría",
                stock_inicial,
                entradas,
                salidas,
                stock_actual,
                float(item.costo),
                float(item.costo) * stock_actual
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename=f'reporte_inventario_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.csv'
        )
        
    except ValueError as e:
        logger.error(f"Error de validación en exportación: {str(e)}")
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    except Exception as e:
        logger.error(f"Error al exportar reporte: {str(e)}", exc_info=True)
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/categorias', methods=['GET'])
@login_required
def get_categorias():
    try:
        # Obtener categorías únicas de los items
        categorias = db.session.query(distinct(InventarioItem.categoria))\
            .filter(InventarioItem.categoria.isnot(None))\
            .order_by(InventarioItem.categoria)\
            .all()
        
        # Formatear las categorías para el frontend
        categorias_formateadas = [
            {
                "nombre": categoria[0]
            }
            for categoria in categorias
            if categoria[0]  # Filtrar valores None o vacíos
        ]
        
        logger.info(f"Categorías recuperadas: {len(categorias_formateadas)}")
        return jsonify(categorias_formateadas)
    except Exception as e:
        logger.error(f"Error al obtener categorías: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


    
# inventario/inventario_routes.py

@inventario_bp.route('/api/almacenes', methods=['GET'])
@login_required
def get_almacenes():
    try:
        almacenes = Almacen.query.all()
        return jsonify([almacen.to_dict() for almacen in almacenes])
    except Exception as e:
        logger.error(f"Error al obtener almacenes: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/almacenes', methods=['POST'])
@login_required
def crear_almacen():
    logger.info("Intento de crear un nuevo almacén")
    try:
        if not request.is_json:
            return jsonify({"error": "Se requiere contenido JSON"}), 400
            
        data = request.get_json()
        logger.debug(f"Datos recibidos: {data}")
        
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        nuevo_almacen = Almacen(
            nombre=data['nombre'],
            ubicacion=data.get('ubicacion'),
            capacidad=float(data.get('capacidad', 0)),
            cuenta_inventario=data.get('cuenta_inventario'),
            es_principal=data.get('es_principal', False),
            descripcion=data.get('descripcion')
        )

        db.session.add(nuevo_almacen)
        db.session.commit()
        logger.info(f"Almacén creado exitosamente: {nuevo_almacen.id}")
        
        return jsonify(nuevo_almacen.to_dict()), 201

    except ValueError as e:
        db.session.rollback()
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear almacén: {str(e)}")
        return jsonify({"error": "Error al crear el almacén"}), 500 

# Agregar estas rutas a inventario_routes.py

@inventario_bp.route('/api/tipos-item', methods=['GET'])
@login_required
def get_tipos_item():
    try:
        tipos = TipoItem.query.all()
        return jsonify([{
            'id': tipo.id,
            'nombre': tipo.nombre,
            'tipo': tipo.tipo,
            'estatus': tipo.estatus,
            'descripcion': tipo.descripcion,
            'es_vendible': tipo.es_vendible,
            'usa_itbis': tipo.usa_itbis,
            'modifica_precio': tipo.modifica_precio,
            'modifica_impuestos': tipo.modifica_impuestos,
            'le_aplica_descuento': tipo.le_aplica_descuento,
            'precio_negativo': tipo.precio_negativo,
            'usa_margen_ganancia': tipo.usa_margen_ganancia,
            'usa_precio_moneda': tipo.usa_precio_moneda,
            'no_venta_costo_pp': tipo.no_venta_costo_pp,
            'gasto_incurrido_para_el_cliente': tipo.gasto_incurrido_para_el_cliente,
            'es_comprable': tipo.es_comprable,
            'proporcionalidad_del_itbis': tipo.proporcionalidad_del_itbis,
            'itbis': tipo.itbis,
            'otros_impuestos': tipo.otros_impuestos,
            'no_modifica_precio': tipo.no_modifica_precio,
            'modifica_costo': tipo.modifica_costo
        } for tipo in tipos])
    except Exception as e:
        logger.error(f"Error al obtener tipos de item: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/tipos-item', methods=['POST'])
@login_required
def crear_tipo_item():
    try:
        if not request.is_json:
            return jsonify({"error": "Se requiere contenido JSON"}), 400
            
        data = request.get_json()
        logger.debug(f"Datos recibidos para tipo: {data}")
        
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        nuevo_tipo = TipoItem(
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo', 'bien'),
            estatus=data.get('estatus', 'activo'),
            es_vendible=data.get('es_vendible', True),
            usa_itbis=data.get('usa_itbis', True),
            modifica_precio=data.get('modifica_precio', False),
            modifica_impuestos=data.get('modifica_impuestos', False),
            le_aplica_descuento=data.get('le_aplica_descuento', True),
            precio_negativo=data.get('precio_negativo', False),
            usa_margen_ganancia=data.get('usa_margen_ganancia', True),
            usa_precio_moneda=data.get('usa_precio_moneda', False),
            no_venta_costo_pp=data.get('no_venta_costo_pp', False),
            gasto_incurrido_para_el_cliente=data.get('gasto_incurrido_para_el_cliente', False),
            es_comprable=data.get('es_comprable', True),
            proporcionalidad_del_itbis=data.get('proporcionalidad_del_itbis', False),
            itbis=data.get('itbis', True),
            otros_impuestos=data.get('otros_impuestos', False),
            no_modifica_precio=data.get('no_modifica_precio', False),
            modifica_costo=data.get('modifica_costo', True)
        )

        db.session.add(nuevo_tipo)
        db.session.commit()
        
        logger.info(f"Tipo de item creado exitosamente: {nuevo_tipo.id}")
        
        return jsonify(nuevo_tipo.to_dict()), 201

    except ValueError as e:
        db.session.rollback()
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear tipo de item: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    


# Remover la ruta duplicada si existe
# @inventario_bp.route('/api/entrada-almacen', methods=['POST'])

# Rutas para Entradas
@inventario_bp.route('/api/entradas', methods=['GET'])
@login_required
def get_entradas():
    try:
        movimientos = MovimientoInventario.query.filter_by(tipo='entrada').all()
        
        if not movimientos:
            return jsonify([]), 200  # Retorna lista vacía si no hay entradas
            
        entradas = []
        for movimiento in movimientos:
            entrada = {
                'id': movimiento.id,
                'numero': f'ENT-{movimiento.id:04d}',
                'fecha': movimiento.fecha.strftime('%Y-%m-%d'),
                'proveedor': movimiento.item.proveedor if movimiento.item else 'N/A',
                'totalItems': 1,
                'estado': 'Completado'
            }
            entradas.append(entrada)
        
        return jsonify(entradas), 200
        
    except Exception as e:
        logger.error(f"Error al obtener entradas: {str(e)}")
        return jsonify({"error": "Error al obtener las entradas"}), 500

@inventario_bp.route('/api/entradas', methods=['POST'])
@login_required
def crear_entrada():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        logger.info(f"Datos recibidos para crear entrada: {data}")
        
        # Validar items
        if not data.get('items'):
            return jsonify({"error": "Se requiere al menos un item"}), 400
            
        # Crear los movimientos de entrada
        for item_data in data['items']:
            # Aquí deberías buscar el item por nombre o código según tu lógica
            item = InventarioItem.query.filter_by(nombre=item_data['nombre']).first()
            if not item:
                return jsonify({"error": f"Item no encontrado: {item_data['nombre']}"}), 404
            
            movimiento = MovimientoInventario(
                item_id=item.id,
                tipo='entrada',
                cantidad=item_data['cantidad'],
                fecha=datetime.utcnow(),
                usuario_id=current_user.id
            )
            db.session.add(movimiento)
            
            # Actualizar stock
            item.stock += item_data['cantidad']
        
        db.session.commit()
        return jsonify({"mensaje": "Entrada creada exitosamente"}), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear entrada: {str(e)}")
        return jsonify({"error": str(e)}), 500

@inventario_bp.route('/api/entradas/<int:entrada_id>', methods=['GET'])
@login_required
def get_entrada(entrada_id):
    try:
        movimiento = MovimientoInventario.query.get_or_404(entrada_id)
        entrada = {
            'id': movimiento.id,
            'numero': f'ENT-{movimiento.id:04d}',
            'fecha': movimiento.fecha.strftime('%Y-%m-%d'),
            'proveedor': movimiento.item.proveedor if movimiento.item else 'N/A',
            'orden_compra': '',
            'factura': '',
            'expediente': '',
            'almacen_id': '',
            'documento': '',
            'referencia': '',
            'nota': '',
            'concepto': 'compra',
            'estatus': 'en-almacen',
            'items': [{
                'nombre': movimiento.item.nombre if movimiento.item else '',
                'cantidad': movimiento.cantidad,
                'costo': movimiento.item.costo if movimiento.item else 0
            }]
        }
        return jsonify(entrada)
    except Exception as e:
        logger.error(f"Error al obtener entrada {entrada_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@inventario_bp.route('/api/entradas/<int:entrada_id>', methods=['DELETE'])
@login_required
def eliminar_entrada(entrada_id):
    try:
        movimiento = MovimientoInventario.query.get_or_404(entrada_id)
        
        # Revertir el cambio en el stock
        if movimiento.item:
            movimiento.item.stock -= movimiento.cantidad
        
        db.session.delete(movimiento)
        db.session.commit()
        
        return jsonify({"mensaje": "Entrada eliminada exitosamente"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar entrada {entrada_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/entradas/count', methods=['GET'])
@login_required
def get_entradas_count():
    try:
        count = MovimientoInventario.query.filter_by(tipo='entrada').count()
        return jsonify({"count": count})
    except Exception as e:
        logger.error(f"Error al obtener conteo de entradas: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500    
    
@inventario_bp.route('/api/items-select', methods=['GET'])
@login_required
def get_items_select():
    try:
        # Filtrar solo por productos activos si es necesario
        items = InventarioItem.query.all()
        return jsonify([{
            'id': item.id,
            'nombre': item.nombre,
            'codigo': item.codigo,
            'precio': item.precio,
            'costo': item.costo,
            'stock': item.stock
        } for item in items])
    except Exception as e:
        logger.error(f"Error al obtener items: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    
@inventario_bp.route('/api/ajustes', methods=['POST'])
@login_required
def crear_ajuste():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        item_id = data.get('item_id')
        cantidad_nueva = data.get('cantidad_nueva')
        motivo = data.get('motivo')
        
        if not all([item_id, cantidad_nueva, motivo]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        item = InventarioItem.query.get_or_404(item_id)
        
        # Crear el ajuste
        ajuste = AjusteInventario(
            item_id=item_id,
            cantidad_anterior=item.stock,
            cantidad_nueva=int(cantidad_nueva),
            motivo=motivo,
            usuario_id=current_user.id
        )
        
        # Actualizar el stock del item
        item.stock = int(cantidad_nueva)
        
        db.session.add(ajuste)
        db.session.commit()
        
        return jsonify({"mensaje": "Ajuste realizado exitosamente"}), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear ajuste: {str(e)}")
        return jsonify({"error": str(e)}), 500    
    
@inventario_bp.route('/api/categorias-item', methods=['GET'])
@login_required
def get_categorias_item():
    try:
        # Asegurarse de que la consulta funcione incluso si la tabla está vacía
        categorias = CategoriaItem.query.all()
        # Añadir logging para debug
        logger.info(f"Categorías encontradas: {len(categorias)}")
        
        return jsonify([{
            'id': categoria.id,
            'nombre': categoria.nombre,
            'estatus': categoria.estatus,
            'descripcion': categoria.descripcion
        } for categoria in categorias])
    except Exception as e:
        logger.error(f"Error al obtener categorías: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/categorias-item/<int:categoria_id>', methods=['GET'])
@login_required
def get_categoria_item(categoria_id):
    try:
        categoria = TipoItem.query.get_or_404(categoria_id)
        return jsonify(categoria.to_dict())
    except Exception as e:
        logger.error(f"Error al obtener categoría {categoria_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/categorias-item/<int:categoria_id>', methods=['DELETE'])
@login_required
def eliminar_categoria_item(categoria_id):
    try:
        categoria = CategoriaItem.query.get_or_404(categoria_id)
        db.session.delete(categoria)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar categoría {categoria_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500     
    
@inventario_bp.route('/api/categorias-item/<int:categoria_id>', methods=['PUT'])
@login_required
def actualizar_categoria_item(categoria_id):
    try:
        categoria = CategoriaItem.query.get_or_404(categoria_id)
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        # Actualizar los campos
        if 'nombre' in data:
            categoria.nombre = data['nombre']
        if 'descripcion' in data:
            categoria.descripcion = data['descripcion']
        if 'estatus' in data:
            categoria.estatus = data['estatus']
            
        db.session.commit()
        
        return jsonify(categoria.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar categoría {categoria_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500   
    
@inventario_bp.route('/api/categorias-item', methods=['POST'])
@login_required
def crear_categoria_item():
    try:
        data = request.get_json()
        logger.info(f"Datos recibidos para nueva categoría: {data}")
        
        if not data or not data.get('nombre'):
            logger.error("Datos inválidos: falta el nombre")
            return jsonify({"error": "El nombre es requerido"}), 400

        # Verificar si ya existe una categoría con ese nombre
        existe = CategoriaItem.query.filter_by(nombre=data['nombre']).first()
        if existe:
            logger.error(f"Ya existe una categoría con el nombre: {data['nombre']}")
            return jsonify({"error": "Ya existe una categoría con ese nombre"}), 400

        # Crear nueva categoría
        nueva_categoria = CategoriaItem(
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            estatus=data.get('estatus', 'activo')
        )
        
        # Log antes de guardar
        logger.info(f"Intentando guardar categoría: {nueva_categoria.nombre}")
        
        # Guardar en la base de datos
        db.session.add(nueva_categoria)
        db.session.flush()  # Para obtener el ID antes del commit
        
        # Log después de flush
        logger.info(f"Categoría en sesión con ID: {nueva_categoria.id}")
        
        # Commit final
        db.session.commit()
        
        # Log después de commit
        logger.info(f"Categoría guardada exitosamente: {nueva_categoria.to_dict()}")
        
        # Retornar la categoría creada
        return jsonify(nueva_categoria.to_dict()), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Error de integridad: {str(e)}")
        return jsonify({"error": "Ya existe una categoría con ese nombre"}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear categoría: {str(e)}")
        return jsonify({"error": str(e)}), 500 
    
@inventario_bp.route('/api/inventario-actual')
@login_required
def get_inventario_actual():
    try:
        items = InventarioItem.query.all()
        logger.info(f"Encontrados {len(items)} items en inventario")
        
        inventario = []
        items_stock_bajo = 0
        items_sin_stock = 0
        items_stock_normal = 0
        items_stock_alto = 0
        
        for item in items:
            stock_actual = item.stock
            
            # Obtener movimientos del item si es necesario
            movimientos = MovimientoInventario.query.filter_by(item_id=item.id).all()
            for mov in movimientos:
                if mov.tipo == 'entrada':
                    stock_actual += mov.cantidad
                elif mov.tipo == 'salida':
                    stock_actual -= mov.cantidad
            
            # Determinar el estado del stock
            stock_bajo = 1 <= stock_actual <= 5
            
            if stock_actual <= 0:
                items_sin_stock += 1
            elif stock_bajo:
                items_stock_bajo += 1
            elif item.stock_maximo and stock_actual >= item.stock_maximo:
                items_stock_alto += 1
            else:
                items_stock_normal += 1
            
            inventario.append({
                'id': item.id,
                'codigo': item.codigo,
                'nombre': item.nombre,
                'categoria': item.categoria,
                'stock_actual': stock_actual,
                'stock_minimo': item.stock_minimo,
                'stock_maximo': item.stock_maximo,
                'costo': float(item.costo) if item.costo else 0,
                'precio': float(item.precio) if item.precio else 0,
                'valor_total': float(item.costo * stock_actual) if item.costo else 0,
                'stock_bajo': stock_bajo
            })

        response_data = {
            'items': inventario,
            'estadisticas': {
                'total_items': len(inventario),
                'items_stock_bajo': items_stock_bajo,
                'items_sin_stock': items_sin_stock,
                'items_stock_normal': items_stock_normal,
                'items_stock_alto': items_stock_alto
            }
        }
        
        logger.info(f"Estadísticas: {response_data['estadisticas']}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error al obtener inventario actual: {str(e)}")
        return jsonify({"error": f"Error al obtener inventario: {str(e)}"}), 500

# Manejo de errores
@inventario_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Recurso no encontrado"}), 404

@inventario_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.error(f'Error del servidor: {str(error)}')
    return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.errorhandler(Exception)
def handle_exception(e):
    current_app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({"error": "Error interno del servidor"}), 500