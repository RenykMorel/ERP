from flask import render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import distinct  
from datetime import datetime
from . import inventario_bp
from .inventario_models import InventarioItem, MovimientoInventario, AjusteInventario, TipoItem, Almacen
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
        
        # Convertir campos numéricos vacíos a None o 0 según corresponda
        stock = int(data.get('stock')) if data.get('stock') and data.get('stock').strip() else 0
        stock_minimo = int(data.get('stock_minimo')) if data.get('stock_minimo') and data.get('stock_minimo').strip() else 0
        stock_maximo = int(data.get('stock_maximo')) if data.get('stock_maximo') and data.get('stock_maximo').strip() else None
        
        # Validar campos requeridos
        if not all([data.get('nombre'), data.get('tipo'), data.get('costo'), 
                   data.get('itbis'), data.get('margen'), data.get('precio')]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        new_item = InventarioItem(
            codigo=data.get('codigo') if data.get('codigo') else None,
            nombre=data['nombre'],
            tipo=data['tipo'],
            costo=float(data['costo']),
            itbis=float(data['itbis']),
            margen=float(data['margen']),
            precio=float(data['precio']),
            descripcion=data.get('descripcion') or None,
            categoria=data.get('categoria') or None,
            proveedor=data.get('proveedor') or None,
            marca=data.get('marca') or None,
            unidad_medida=data.get('unidad_medida') or None,
            stock=stock,
            stock_minimo=stock_minimo,
            stock_maximo=stock_maximo
        )

        db.session.add(new_item)
        db.session.commit()
        
        logger.info(f"Item creado exitosamente: {new_item.id}")
        return jsonify(new_item.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({"error": "Error en los datos proporcionados. Verifique los campos numéricos."}), 400
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Error de integridad: {str(e)}")
        return jsonify({"error": "Ya existe un item con ese código"}), 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear item: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    item = InventarioItem.query.get_or_404(item_id)
    data = request.json
    try:
        item.update_from_dict(data)
        db.session.commit()
        return jsonify(item.to_dict())
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Error de integridad al actualizar item: {str(e)}")
        return jsonify({"error": "Ya existe un item con ese código"}), 400
    except ValueError as e:
        current_app.logger.error(f"Error de validación al actualizar item: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error inesperado al actualizar item: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

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
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        query = MovimientoInventario.query.filter(
            MovimientoInventario.fecha.between(fecha_inicio, fecha_fin)
        )
        
        if categoria:
            query = query.join(InventarioItem).filter(InventarioItem.categoria == categoria)
        
        movimientos = query.all()
        
        reporte = {}
        for movimiento in movimientos:
            if movimiento.item_id not in reporte:
                reporte[movimiento.item_id] = {
                    "item": movimiento.item.to_dict(),
                    "entradas": 0,
                    "salidas": 0
                }
            if movimiento.tipo == 'entrada':
                reporte[movimiento.item_id]["entradas"] += movimiento.cantidad
            else:
                reporte[movimiento.item_id]["salidas"] += movimiento.cantidad
        
        return jsonify(list(reporte.values()))
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    except Exception as e:
        current_app.logger.error(f"Error al generar reporte: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/categorias', methods=['GET'])
@login_required
def get_categorias():
    try:
        categorias = db.session.query(distinct(InventarioItem.categoria)).all()
        categorias = [categoria[0] for categoria in categorias if categoria[0]]  # Filtra los valores None o vacíos
        return jsonify(categorias)
    except Exception as e:
        current_app.logger.error(f"Error al obtener categorías: {str(e)}")
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
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        query = MovimientoInventario.query.filter(
            MovimientoInventario.fecha.between(fecha_inicio, fecha_fin)
        )
        
        if categoria:
            query = query.join(InventarioItem).filter(InventarioItem.categoria == categoria)
        
        movimientos = query.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Código', 'Nombre', 'Categoría', 'Entradas', 'Salidas', 'Stock Final'])
        
        reporte = {}
        for movimiento in movimientos:
            if movimiento.item_id not in reporte:
                reporte[movimiento.item_id] = {
                    "item": movimiento.item,
                    "entradas": 0,
                    "salidas": 0
                }
            if movimiento.tipo == 'entrada':
                reporte[movimiento.item_id]["entradas"] += movimiento.cantidad
            else:
                reporte[movimiento.item_id]["salidas"] += movimiento.cantidad
        
        for item_id, data in reporte.items():
            item = data['item']
            writer.writerow([
                item.codigo,
                item.nombre,
                item.categoria,
                data['entradas'],
                data['salidas'],
                item.stock
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename='reporte_inventario.csv'
        )
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    except Exception as e:
        current_app.logger.error(f"Error al exportar reporte: {str(e)}")
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
        return jsonify([tipo.to_dict() for tipo in tipos])
    except Exception as e:
        logger.error(f"Error al obtener tipos de item: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@inventario_bp.route('/api/tipos-item', methods=['POST'])
@login_required
def crear_tipo_item():
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        nuevo_tipo = TipoItem(
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo'),  # 'servicio', 'bien', 'cargo'
            estatus=data.get('estatus', 'activo'),
            # Configuración para la venta
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
            # Configuración para la compra
            es_comprable=data.get('es_comprable', True),
            proporcionalidad_del_itbis=data.get('proporcionalidad_del_itbis', False),
            itbis=data.get('itbis', True),
            otros_impuestos=data.get('otros_impuestos', False),
            no_modifica_precio=data.get('no_modifica_precio', False),
            modifica_costo=data.get('modifica_costo', True)
        )

        db.session.add(nuevo_tipo)
        db.session.commit()
        
        # Retornar el nuevo tipo creado
        return jsonify(nuevo_tipo.to_dict()), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe un tipo de item con ese nombre"}), 400
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
        categorias = TipoItem.query.all()
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
def delete_categoria_item(categoria_id):
    try:
        categoria = TipoItem.query.get_or_404(categoria_id)
        db.session.delete(categoria)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar categoría {categoria_id}: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500       
    
@inventario_bp.route('/api/categorias-item', methods=['POST'])
@login_required
def crear_categoria_item():
    try:
        if not request.is_json:
            return jsonify({"error": "Se requiere contenido JSON"}), 400
            
        data = request.get_json()
        logger.debug(f"Datos recibidos: {data}")
        
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        nueva_categoria = TipoItem(
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

        db.session.add(nueva_categoria)
        db.session.commit()
        
        logger.info(f"Categoría creada exitosamente: {nueva_categoria.id}")
        
        return jsonify(nueva_categoria.to_dict()), 201

    except ValueError as e:
        db.session.rollback()
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear categoría: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500  
    
    

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