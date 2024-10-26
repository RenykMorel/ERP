from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from . import inventario_bp
from .inventario_models import InventarioItem, MovimientoInventario, AjusteInventario
from extensions import db
import logging

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