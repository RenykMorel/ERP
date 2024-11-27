#routes.py en la carpeta de contabilidad
from flask import render_template, request, jsonify, abort, send_file, current_app
from . import contabilidad_bp
from .models import (ContabilidadCuenta, AsientoDiario, MayorGeneral, 
                    BalanzaComprobacion, EstadoResultados, BalanceGeneral, 
                    ConfiguracionContable, FlujoCaja)
from app import db
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from io import BytesIO
import os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
import logging
from .models import ConfiguracionContable


# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definición de errores personalizados
class ContabilidadError(Exception):
    """Clase base para excepciones de contabilidad"""
    pass

class FormatoInvalidoError(ContabilidadError):
    """Excepción para errores de formato en los datos"""
    pass

class DatosIncorrectosError(ContabilidadError):
    """Excepción para datos incorrectos"""
    pass

class BalanceError(ContabilidadError):
    """Excepción para errores de balance"""
    pass

# Configuración para la carga de archivos
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Funciones auxiliares
def validar_cuenta(data):
    """Valida los datos de una cuenta antes de crearla o actualizarla"""
    required_fields = ['numero_cuenta', 'nombre']
    for field in required_fields:
        if field not in data or not data[field]:
            raise FormatoInvalidoError(f"El campo '{field}' es requerido")
    
    if 'origen' in data and data['origen']:
        if data['origen'].upper() not in ['DEBITO', 'CREDITO']:
            raise FormatoInvalidoError("El origen debe ser DEBITO o CREDITO")
    
    if 'categoria' in data and data['categoria']:
        if data['categoria'].upper() not in ['CONTROL', 'AUXILIAR']:
            raise FormatoInvalidoError("La categoría debe ser CONTROL o AUXILIAR")
    
    return True

def validar_asiento(data):
    """Valida los datos de un asiento contable"""
    if not all(key in data for key in ['fecha', 'descripcion', 'detalle']):
        raise FormatoInvalidoError("Faltan campos requeridos en el asiento")
        
    total_debe = sum(float(detalle.get('debe', 0) or 0) for detalle in data['detalle'])
    total_haber = sum(float(detalle.get('haber', 0) or 0) for detalle in data['detalle'])
    
    if round(total_debe, 2) != round(total_haber, 2):
        raise BalanceError("El asiento no está balanceado")
    
    return True

def format_date(date):
    """Formatea una fecha para la base de datos"""
    if isinstance(date, str):
        return datetime.strptime(date, '%Y-%m-%d')
    return date

def format_number(number):
    """Formatea un número para la base de datos"""
    try:
        return float(number or 0)
    except (TypeError, ValueError):
        raise FormatoInvalidoError(f"Valor numérico inválido: {number}")

# Rutas principales
@contabilidad_bp.route('/cuentas')
def lista_cuentas():
    return render_template('contabilidad/cuentas.html')

@contabilidad_bp.route('/api/cuentas', methods=['GET'])
def api_lista_cuentas():
    try:
        cuentas = ContabilidadCuenta.query.order_by(ContabilidadCuenta.numero_cuenta).all()
        return jsonify({
            'success': True,
            'cuentas': [cuenta.to_dict() for cuenta in cuentas]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/cuentas', methods=['POST'])
@login_required
def crear_cuenta():
    try:
        data = request.json
        # Eliminar el id si viene vacío
        if 'id' in data and not data['id']:
            del data['id']
        
        # Asegurarse de que el código está establecido
        if not data.get('codigo'):
            data['codigo'] = data.get('numero_cuenta')

        cuenta = ContabilidadCuenta(**data)
        cuenta.calcular_nivel_y_padre()
        
        db.session.add(cuenta)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cuenta creada exitosamente',
            'cuenta': cuenta.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@contabilidad_bp.route('/api/cuentas/<int:cuenta_id>', methods=['GET'])
def obtener_cuenta(cuenta_id):
    try:
        cuenta = ContabilidadCuenta.query.get_or_404(cuenta_id)
        return jsonify({
            'success': True,
            'cuenta': cuenta.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/cuentas/<int:cuenta_id>', methods=['PUT'])
@login_required
def actualizar_cuenta(cuenta_id):
    try:
        cuenta = ContabilidadCuenta.query.get_or_404(cuenta_id)
        data = request.json
        
        # Evitar cambiar el ID
        data.pop('id', None)
        data.pop('fecha_creacion', None)
        data.pop('fecha_modificacion', None)

        # Actualizar los campos permitidos
        campos_actualizables = [
            'codigo', 'numero_cuenta', 'nombre', 'origen', 'categoria',
            'nivel', 'padre_id', 'tipo', 'grupo', 'descripcion',
            'estatus', 'flujo_efectivo', 'corriente', 'balance_general'
        ]

        for campo in campos_actualizables:
            if campo in data:
                setattr(cuenta, campo, data[campo])

        cuenta.calcular_nivel_y_padre()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cuenta actualizada exitosamente',
            'cuenta': cuenta.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@contabilidad_bp.route('/api/cuentas/<int:cuenta_id>', methods=['DELETE'])
def eliminar_cuenta(cuenta_id):
    try:
        cuenta = ContabilidadCuenta.query.get_or_404(cuenta_id)
        
        # Verificar dependencias
        if ContabilidadCuenta.query.filter_by(padre_id=cuenta.numero_cuenta).first():
            return jsonify({
                'success': False,
                'error': 'No se puede eliminar una cuenta que tiene subcuentas'
            }), 400
        
        db.session.delete(cuenta)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cuenta eliminada exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Ruta para búsqueda de cuentas
@contabilidad_bp.route('/api/buscar-cuentas', methods=['GET'])
def api_buscar_cuentas():
    try:
        numero = request.args.get('numero', '')
        nombre = request.args.get('nombre', '')
        categoria = request.args.get('categoria', '')
        
        # Agregar logs
        logger.info(f"Parámetros de búsqueda: numero={numero}, nombre={nombre}, categoria={categoria}")
        
        query = ContabilidadCuenta.query
        
        # Verificar si hay registros antes de los filtros
        total_cuentas = query.count()
        logger.info(f"Total de cuentas antes de filtros: {total_cuentas}")
        
        if numero:
            query = query.filter(ContabilidadCuenta.numero_cuenta.ilike(f'%{numero}%'))
        if nombre:
            query = query.filter(ContabilidadCuenta.nombre.ilike(f'%{nombre}%'))
        if categoria:
            query = query.filter(ContabilidadCuenta.categoria == categoria)
            
        cuentas = query.order_by(ContabilidadCuenta.numero_cuenta).all()
        
        # Log del resultado
        logger.info(f"Cuentas encontradas: {len(cuentas)}")
        for cuenta in cuentas[:5]:  # Mostrar las primeras 5 cuentas como ejemplo
            logger.info(f"Cuenta: {cuenta.numero_cuenta} - {cuenta.nombre}")
            
        return jsonify({
            'success': True,
            'cuentas': [{
                'id': cuenta.id,
                'numero_cuenta': cuenta.numero_cuenta,
                'nombre': cuenta.nombre,
                'padre_id': cuenta.padre_id,
                'tipo': cuenta.tipo or '',
                'categoria': cuenta.categoria,
                'grupo': cuenta.grupo or '',
            } for cuenta in cuentas]
        })
    except Exception as e:
        logger.error(f"Error en búsqueda de cuentas: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
        
@contabilidad_bp.route('/api/diagnostico-cuentas')
def diagnostico_cuentas():
    try:
        # Contar total de cuentas
        total = ContabilidadCuenta.query.count()
        
        # Obtener algunos ejemplos
        ejemplos = ContabilidadCuenta.query.limit(5).all()
        
        return jsonify({
            'success': True,
            'total_cuentas': total,
            'ejemplos': [{
                'id': c.id,
                'numero_cuenta': c.numero_cuenta,
                'nombre': c.nombre,
                'categoria': c.categoria
            } for c in ejemplos]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })        

@contabilidad_bp.route('/api/cargar-catalogo', methods=['POST'])
@login_required
def cargar_catalogo():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No se encontró el archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400

    if file and allowed_file(file.filename):
        try:
            # Leer el archivo Excel
            df = pd.read_excel(file)
            
            # Imprimir información para debug
            logger.info(f"Columnas detectadas: {df.columns.tolist()}")
            logger.info(f"Primeras filas:\n{df.head()}")

            # Limpiar y preparar los datos
            df = df.dropna(subset=['No. Cuenta', 'Nombre'])  # Eliminar filas sin número de cuenta o nombre
            df = df.fillna('')  # Rellenar valores NaN con cadenas vacías

            cuentas_creadas = 0
            cuentas_actualizadas = 0
            errores = []

            for index, row in df.iterrows():
                try:
                    # Convertir y limpiar datos
                    numero_cuenta = str(row['No. Cuenta']).strip()
                    nombre = str(row['Nombre']).strip()
                    padre_id = str(row['Cuenta Padre']).strip() if row['Cuenta Padre'] else None
                    tipo = str(row['Tipo']).strip() if row['Tipo'] else 'Detalle'
                    categoria = str(row['Categoria']).strip() if row['Categoria'] else 'CONTROL'
                    grupo = str(row['Grupo']).strip() if row['Grupo'] else None

                    # Verificar si la cuenta existe
                    cuenta = ContabilidadCuenta.query.filter_by(numero_cuenta=numero_cuenta).first()

                    if cuenta:
                        # Actualizar cuenta existente
                        cuenta.nombre = nombre
                        cuenta.padre_id = padre_id
                        cuenta.tipo = tipo
                        cuenta.categoria = categoria
                        cuenta.grupo = grupo
                        cuenta.calcular_nivel_y_padre()
                        cuentas_actualizadas += 1
                        logger.info(f"Cuenta actualizada: {numero_cuenta}")
                    else:
                        # Crear nueva cuenta
                        nueva_cuenta = ContabilidadCuenta(
                            numero_cuenta=numero_cuenta,
                            codigo=numero_cuenta,
                            nombre=nombre,
                            padre_id=padre_id,
                            tipo=tipo,
                            categoria=categoria,
                            grupo=grupo,
                            estatus='Activo'
                        )
                        nueva_cuenta.calcular_nivel_y_padre()
                        db.session.add(nueva_cuenta)
                        cuentas_creadas += 1
                        logger.info(f"Cuenta creada: {numero_cuenta}")

                    # Commit cada 100 registros
                    if (cuentas_creadas + cuentas_actualizadas) % 100 == 0:
                        db.session.commit()

                except Exception as e:
                    error_msg = f"Error en fila {index + 2}: {str(e)} - Cuenta: {numero_cuenta}"
                    logger.error(error_msg)
                    errores.append(error_msg)
                    continue

            # Commit final
            db.session.commit()

            logger.info(f"Proceso completado: {cuentas_creadas} creadas, {cuentas_actualizadas} actualizadas")
            
            return jsonify({
                'success': True,
                'message': f"Proceso completado exitosamente.\nCuentas creadas: {cuentas_creadas}, actualizadas: {cuentas_actualizadas}",
                'detalles': {
                    'cuentas_creadas': cuentas_creadas,
                    'cuentas_actualizadas': cuentas_actualizadas,
                    'errores': errores,
                    'data_preview': df.head().to_dict('records')
                }
            })

        except Exception as e:
            db.session.rollback()
            error_msg = f"Error al procesar el archivo: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

    return jsonify({'success': False, 'error': 'Tipo de archivo no permitido'}), 400

@contabilidad_bp.route('/api/descargar-catalogo', methods=['GET'])
def descargar_catalogo():
    try:
        cuentas = ContabilidadCuenta.query.order_by(ContabilidadCuenta.numero_cuenta).all()
        
        df = pd.DataFrame([{
            'No. Cue': cuenta.numero_cuenta,
            'Nombre': cuenta.nombre,
            'Cuenta': cuenta.padre_id,
            'Tipo': cuenta.tipo,
            'Catego': cuenta.categoria,
            'Grupo': cuenta.grupo
        } for cuenta in cuentas])

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Catálogo de Cuentas')
            
            # Ajustar el ancho de las columnas
            worksheet = writer.sheets['Catálogo de Cuentas']
            for idx, col in enumerate(df):
                max_length = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='catalogo_cuentas.xlsx'
        )

    except Exception as e:
        logger.error(f"Error al descargar el catálogo: {str(e)}")
        
        return jsonify({'success': False, 'error': f"Error al descargar el catálogo: {str(e)}"}), 500

# Manejo de errores global
@contabilidad_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'error': 'Recurso no encontrado'
    }), 404

@contabilidad_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor'
    }), 500

# Rutas adicionales para manejar otras funcionalidades contables

@contabilidad_bp.route('/api/asientos', methods=['POST'])
@login_required
def crear_asiento():
    try:
        data = request.json
        validar_asiento(data)
        
        asiento = AsientoDiario(
            fecha=format_date(data['fecha']),
            descripcion=data['descripcion'],
            usuario_id=current_user.id
        )
        
        for detalle in data['detalle']:
            asiento.detalles.append(AsientoDiarioDetalle(
                cuenta_id=detalle['cuenta_id'],
                debe=format_number(detalle['debe']),
                haber=format_number(detalle['haber'])
            ))
        
        db.session.add(asiento)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Asiento creado exitosamente',
            'asiento_id': asiento.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@contabilidad_bp.route('/api/asientos', methods=['GET'])
def listar_asientos():
    try:
        asientos = AsientoDiario.query.order_by(AsientoDiario.fecha.desc()).all()
        return jsonify({
            'success': True,
            'asientos': [asiento.to_dict() for asiento in asientos]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# En routes.py de la carpeta contabilidad

@contabilidad_bp.route('/mayor_general')
@login_required
def ver_mayor_general():
    """Vista principal del mayor general"""
    return render_template('contabilidad/mayor_general.html')

@contabilidad_bp.route('/api/mayor_general/movimientos', methods=['GET'])
@login_required
def obtener_movimientos_mayor():
    """Obtiene los movimientos del mayor general"""
    try:
        cuenta_id = request.args.get('cuenta_id')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        # Construir la consulta base
        query = db.session.query(
            AsientoDiarioDetalle,
            AsientoDiario.fecha,
            AsientoDiario.descripcion
        ).join(
            AsientoDiario,
            AsientoDiario.id == AsientoDiarioDetalle.asiento_id
        ).join(
            ContabilidadCuenta,
            ContabilidadCuenta.id == AsientoDiarioDetalle.cuenta_id
        )
        
        # Aplicar filtros
        if cuenta_id:
            query = query.filter(AsientoDiarioDetalle.cuenta_id == cuenta_id)
        if fecha_inicio:
            query = query.filter(AsientoDiario.fecha >= datetime.strptime(fecha_inicio, '%Y-%m-%d'))
        if fecha_fin:
            query = query.filter(AsientoDiario.fecha <= datetime.strptime(fecha_fin, '%Y-%m-%d'))
        
        # Ordenar por cuenta y fecha
        query = query.order_by(
            ContabilidadCuenta.numero_cuenta,
            AsientoDiario.fecha,
            AsientoDiario.id
        )
        
        # Ejecutar la consulta
        resultados = query.all()
        
        # Procesar los resultados
        mayor_general = {}
        for detalle, fecha, descripcion in resultados:
            cuenta_id = detalle.cuenta_id
            cuenta = detalle.cuenta
            
            if cuenta_id not in mayor_general:
                mayor_general[cuenta_id] = {
                    'cuenta': cuenta.numero_cuenta + ' - ' + cuenta.nombre,
                    'movimientos': [],
                    'saldo': 0
                }
            
            saldo = mayor_general[cuenta_id]['saldo']
            debe = float(detalle.debe) if detalle.debe else 0
            haber = float(detalle.haber) if detalle.haber else 0
            
            # Calcular nuevo saldo según la naturaleza de la cuenta
            if cuenta.origen == 'DEBITO':
                saldo = saldo + debe - haber
            else:
                saldo = saldo - debe + haber
                
            mayor_general[cuenta_id]['saldo'] = saldo
            mayor_general[cuenta_id]['movimientos'].append({
                'fecha': fecha.strftime('%Y-%m-%d'),
                'descripcion': descripcion,
                'debe': debe,
                'haber': haber,
                'saldo': saldo
            })
        
        return jsonify({
            'success': True,
            'data': list(mayor_general.values())
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo mayor general: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/mayor_general/cuentas', methods=['GET'])
@login_required
def obtener_cuentas_mayor():
    """Obtiene la lista de cuentas para el mayor general"""
    try:
        cuentas = ContabilidadCuenta.query.filter_by(
            categoria='AUXILIAR'  # Solo cuentas auxiliares
        ).order_by(
            ContabilidadCuenta.numero_cuenta
        ).all()
        
        return jsonify({
            'success': True,
            'cuentas': [{
                'id': cuenta.id,
                'codigo': cuenta.numero_cuenta,
                'nombre': cuenta.nombre
            } for cuenta in cuentas]
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo cuentas para mayor: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
# Agregar esta ruta al archivo routes.py en la carpeta de contabilidad

@contabilidad_bp.route('/diario')
@login_required
def diario_contable():
    """Vista principal del diario contable"""
    return render_template('contabilidad/diario.html')

@contabilidad_bp.route('/api/diario', methods=['GET'])
@login_required
def listar_asientos_diario():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        descripcion = request.args.get('descripcion')
        cuenta_id = request.args.get('cuenta_id')
        
        query = AsientoDiario.query
        
        if fecha_inicio:
            query = query.filter(AsientoDiario.fecha >= datetime.strptime(fecha_inicio, '%Y-%m-%d'))
        if fecha_fin:
            query = query.filter(AsientoDiario.fecha <= datetime.strptime(fecha_fin, '%Y-%m-%d'))
        if descripcion:
            query = query.filter(AsientoDiario.descripcion.ilike(f'%{descripcion}%'))
        if cuenta_id:
            query = query.join(AsientoDiarioDetalle).filter(AsientoDiarioDetalle.cuenta_id == cuenta_id)
            
        asientos = query.order_by(AsientoDiario.fecha.desc(), AsientoDiario.id.desc()).all()
        
        return jsonify({
            'success': True,
            'asientos': [{
                'id': asiento.id,
                'fecha': asiento.fecha.strftime('%Y-%m-%d'),
                'descripcion': asiento.descripcion,
                'detalles': [{
                    'cuenta_id': detalle.cuenta_id,
                    'cuenta_nombre': detalle.cuenta.nombre if detalle.cuenta else 'N/A',
                    'debe': float(detalle.debe) if detalle.debe else 0,
                    'haber': float(detalle.haber) if detalle.haber else 0
                } for detalle in asiento.detalles]
            } for asiento in asientos]
        })
        
    except Exception as e:
        logger.error(f"Error listando asientos del diario: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error al listar asientos: {str(e)}"
        }), 500

@contabilidad_bp.route('/api/diario', methods=['POST'])
@login_required
def crear_asiento_diario():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not all(key in data for key in ['fecha', 'descripcion', 'detalles']):
            return jsonify({
                'success': False,
                'error': 'Faltan datos requeridos'
            }), 400
            
        # Validar balance de debe y haber
        total_debe = sum(float(detalle.get('debe', 0) or 0) for detalle in data['detalles'])
        total_haber = sum(float(detalle.get('haber', 0) or 0) for detalle in data['detalles'])
        
        if round(total_debe, 2) != round(total_haber, 2):
            return jsonify({
                'success': False,
                'error': 'El asiento no está balanceado. El total del debe debe ser igual al total del haber.'
            }), 400
            
        # Crear el asiento
        nuevo_asiento = AsientoDiario(
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d'),
            descripcion=data['descripcion'],
            usuario_id=current_user.id
        )
        
        # Agregar detalles
        for detalle in data['detalles']:
            nuevo_detalle = AsientoDiarioDetalle(
                cuenta_id=detalle['cuenta_id'],
                debe=detalle.get('debe', 0),
                haber=detalle.get('haber', 0)
            )
            nuevo_asiento.detalles.append(nuevo_detalle)
            
        db.session.add(nuevo_asiento)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Asiento creado exitosamente',
            'asiento': {
                'id': nuevo_asiento.id,
                'fecha': nuevo_asiento.fecha.strftime('%Y-%m-%d'),
                'descripcion': nuevo_asiento.descripcion
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando asiento: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error al crear asiento: {str(e)}"
        }), 500        
        
        

# Agregar estas rutas al archivo routes.py en la carpeta de contabilidad

@contabilidad_bp.route('/balanza_comprobacion')
@login_required
def ver_balanza_comprobacion():
    """Vista principal de la balanza de comprobación"""
    return render_template('contabilidad/balanza_comprobacion.html')

@contabilidad_bp.route('/api/balanza_comprobacion/generar', methods=['GET'])
@login_required
def generar_balanza_comprobacion():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({
                'success': False,
                'error': 'Se requieren fechas de inicio y fin'
            }), 400

        # Convertir fechas
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')

        # Obtener todas las cuentas auxiliares
        cuentas = ContabilidadCuenta.query.filter_by(categoria='AUXILIAR').all()
        
        # Obtener todos los movimientos del período
        movimientos = db.session.query(
            AsientoDiarioDetalle.cuenta_id,
            db.func.sum(AsientoDiarioDetalle.debe).label('total_debe'),
            db.func.sum(AsientoDiarioDetalle.haber).label('total_haber')
        ).join(
            AsientoDiario,
            AsientoDiario.id == AsientoDiarioDetalle.asiento_id
        ).filter(
            AsientoDiario.fecha.between(fecha_inicio, fecha_fin)
        ).group_by(
            AsientoDiarioDetalle.cuenta_id
        ).all()

        # Crear diccionario para almacenar los totales por cuenta
        resultados = {}
        for cuenta in cuentas:
            resultados[cuenta.id] = {
                'cuenta': f"{cuenta.numero_cuenta} - {cuenta.nombre}",
                'origen': cuenta.origen,
                'debe': 0,
                'haber': 0,
                'saldo_deudor': 0,
                'saldo_acreedor': 0
            }

        # Procesar movimientos
        for cuenta_id, total_debe, total_haber in movimientos:
            if cuenta_id in resultados:
                resultados[cuenta_id]['debe'] = float(total_debe or 0)
                resultados[cuenta_id]['haber'] = float(total_haber or 0)
                
                # Calcular saldos según la naturaleza de la cuenta
                total_debe = float(total_debe or 0)
                total_haber = float(total_haber or 0)
                saldo = total_debe - total_haber
                
                if saldo > 0:
                    resultados[cuenta_id]['saldo_deudor'] = abs(saldo)
                    resultados[cuenta_id]['saldo_acreedor'] = 0
                else:
                    resultados[cuenta_id]['saldo_deudor'] = 0
                    resultados[cuenta_id]['saldo_acreedor'] = abs(saldo)

        # Calcular totales
        totales = {
            'debe': sum(r['debe'] for r in resultados.values()),
            'haber': sum(r['haber'] for r in resultados.values()),
            'saldo_deudor': sum(r['saldo_deudor'] for r in resultados.values()),
            'saldo_acreedor': sum(r['saldo_acreedor'] for r in resultados.values())
        }

        # Filtrar cuentas sin movimientos
        balanza = [cuenta for cuenta in resultados.values() 
                  if cuenta['debe'] != 0 or cuenta['haber'] != 0]

        return jsonify({
            'success': True,
            'data': {
                'cuentas': balanza,
                'totales': totales
            }
        })

    except Exception as e:
        logger.error(f"Error generando balanza de comprobación: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Agregar estas rutas al archivo routes.py en la carpeta de contabilidad

@contabilidad_bp.route('/estado_resultados')
@login_required
def ver_estado_resultados():
    """Vista principal del estado de resultados"""
    return render_template('contabilidad/estado_resultados.html')

@contabilidad_bp.route('/api/estado_resultados/generar', methods=['GET'])
@login_required
def generar_estado_resultados():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({
                'success': False,
                'error': 'Se requieren fechas de inicio y fin'
            }), 400

        # Convertir fechas
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')

        # Obtener cuentas de resultados
        ingresos_cuentas = ContabilidadCuenta.query.filter_by(
            tipo='INGRESOS'
        ).all()
        gastos_cuentas = ContabilidadCuenta.query.filter_by(
            tipo='GASTOS'
        ).all()

        # Obtener movimientos del período
        movimientos = db.session.query(
            AsientoDiarioDetalle.cuenta_id,
            ContabilidadCuenta.nombre,
            ContabilidadCuenta.tipo,
            db.func.sum(AsientoDiarioDetalle.debe).label('total_debe'),
            db.func.sum(AsientoDiarioDetalle.haber).label('total_haber')
        ).join(
            ContabilidadCuenta,
            ContabilidadCuenta.id == AsientoDiarioDetalle.cuenta_id
        ).join(
            AsientoDiario,
            AsientoDiario.id == AsientoDiarioDetalle.asiento_id
        ).filter(
            AsientoDiario.fecha.between(fecha_inicio, fecha_fin),
            ContabilidadCuenta.tipo.in_(['INGRESOS', 'GASTOS'])
        ).group_by(
            AsientoDiarioDetalle.cuenta_id,
            ContabilidadCuenta.nombre,
            ContabilidadCuenta.tipo
        ).all()

        # Procesar movimientos
        detalles = []
        total_ingresos = 0
        total_gastos = 0

        for cuenta_id, nombre, tipo, total_debe, total_haber in movimientos:
            total_debe = float(total_debe or 0)
            total_haber = float(total_haber or 0)
            
            if tipo == 'INGRESOS':
                monto = total_haber - total_debe
                total_ingresos += monto
            else:  # GASTOS
                monto = total_debe - total_haber
                total_gastos += monto

            if monto != 0:  # Solo incluir cuentas con movimiento
                detalles.append({
                    'concepto': nombre,
                    'monto': abs(monto),
                    'tipo': tipo.lower()
                })

        # Calcular utilidad
        utilidad = total_ingresos - total_gastos

        # Organizar los detalles
        detalles.sort(key=lambda x: (-x['monto'] if x['tipo'] == 'ingresos' else x['monto']))

        return jsonify({
            'success': True,
            'data': {
                'ingresos': total_ingresos,
                'gastos': total_gastos,
                'utilidad': utilidad,
                'detalles': detalles,
                'periodo': {
                    'inicio': fecha_inicio.strftime('%Y-%m-%d'),
                    'fin': fecha_fin.strftime('%Y-%m-%d')
                }
            }
        })

    except Exception as e:
        logger.error(f"Error generando estado de resultados: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Agregar estas rutas al archivo routes.py en la carpeta de contabilidad

@contabilidad_bp.route('/balance_general')
@login_required
def ver_balance_general():
    """Vista principal del balance general"""
    return render_template('contabilidad/balance_general.html')

@contabilidad_bp.route('/api/balance_general/generar', methods=['GET'])
@login_required
def generar_balance_general():
    try:
        fecha_balance = request.args.get('fecha')
        
        if not fecha_balance:
            return jsonify({
                'success': False,
                'error': 'Se requiere una fecha para el balance'
            }), 400

        fecha = datetime.strptime(fecha_balance, '%Y-%m-%d')

        # Obtener todas las cuentas con sus saldos
        saldos = db.session.query(
            ContabilidadCuenta,
            db.func.sum(AsientoDiarioDetalle.debe).label('total_debe'),
            db.func.sum(AsientoDiarioDetalle.haber).label('total_haber')
        ).join(
            AsientoDiarioDetalle,
            ContabilidadCuenta.id == AsientoDiarioDetalle.cuenta_id
        ).join(
            AsientoDiario,
            AsientoDiario.id == AsientoDiarioDetalle.asiento_id
        ).filter(
            AsientoDiario.fecha <= fecha,
            ContabilidadCuenta.tipo.in_(['ACTIVO', 'PASIVO', 'CAPITAL'])
        ).group_by(
            ContabilidadCuenta.id
        ).all()

        # Inicializar estructuras para el balance
        activos = {
            'circulante': {'cuentas': [], 'total': 0},
            'fijo': {'cuentas': [], 'total': 0},
            'otros': {'cuentas': [], 'total': 0}
        }
        
        pasivos = {
            'corto_plazo': {'cuentas': [], 'total': 0},
            'largo_plazo': {'cuentas': [], 'total': 0}
        }
        
        capital = {
            'cuentas': [],
            'total': 0
        }

        # Procesar saldos
        for cuenta, total_debe, total_haber in saldos:
            total_debe = float(total_debe or 0)
            total_haber = float(total_haber or 0)
            
            if cuenta.tipo == 'ACTIVO':
                saldo = total_debe - total_haber
                if saldo != 0:
                    cuenta_data = {
                        'codigo': cuenta.numero_cuenta,
                        'nombre': cuenta.nombre,
                        'saldo': abs(saldo)
                    }
                    
                    if cuenta.corriente:  # Si es activo circulante
                        activos['circulante']['cuentas'].append(cuenta_data)
                        activos['circulante']['total'] += saldo
                    elif cuenta.tipo == 'FIJO':
                        activos['fijo']['cuentas'].append(cuenta_data)
                        activos['fijo']['total'] += saldo
                    else:
                        activos['otros']['cuentas'].append(cuenta_data)
                        activos['otros']['total'] += saldo
                        
            elif cuenta.tipo == 'PASIVO':
                saldo = total_haber - total_debe
                if saldo != 0:
                    cuenta_data = {
                        'codigo': cuenta.numero_cuenta,
                        'nombre': cuenta.nombre,
                        'saldo': abs(saldo)
                    }
                    
                    if cuenta.corriente:  # Si es pasivo a corto plazo
                        pasivos['corto_plazo']['cuentas'].append(cuenta_data)
                        pasivos['corto_plazo']['total'] += saldo
                    else:
                        pasivos['largo_plazo']['cuentas'].append(cuenta_data)
                        pasivos['largo_plazo']['total'] += saldo
                        
            elif cuenta.tipo == 'CAPITAL':
                saldo = total_haber - total_debe
                if saldo != 0:
                    capital['cuentas'].append({
                        'codigo': cuenta.numero_cuenta,
                        'nombre': cuenta.nombre,
                        'saldo': abs(saldo)
                    })
                    capital['total'] += saldo

        # Calcular totales
        total_activos = (
            activos['circulante']['total'] +
            activos['fijo']['total'] +
            activos['otros']['total']
        )
        
        total_pasivos = (
            pasivos['corto_plazo']['total'] +
            pasivos['largo_plazo']['total']
        )
        
        total_pasivo_capital = total_pasivos + capital['total']

        return jsonify({
            'success': True,
            'data': {
                'activos': activos,
                'pasivos': pasivos,
                'capital': capital,
                'totales': {
                    'activos': total_activos,
                    'pasivos': total_pasivos,
                    'pasivo_capital': total_pasivo_capital
                },
                'fecha': fecha.strftime('%Y-%m-%d')
            }
        })

    except Exception as e:
        logger.error(f"Error generando balance general: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/configuraciones')
@login_required
def ver_configuraciones():
    """Vista principal de configuraciones contables"""
    try:
        configs = ConfiguracionContable.query.all()
        return render_template('contabilidad/configuraciones.html', configs=configs)
    except Exception as e:
        current_app.logger.error(f"Error cargando configuraciones: {str(e)}")
        return render_template('contabilidad/configuraciones.html', configs=[])

@contabilidad_bp.route('/api/configuraciones', methods=['GET'])
@login_required
def obtener_configuraciones():
    """Obtiene todas las configuraciones contables"""
    try:
        configs = ConfiguracionContable.query.all()
        return jsonify({
            'success': True,
            'configuraciones': [{
                'id': config.id,
                'clave': config.clave,
                'valor': config.valor,
                'descripcion': config.descripcion
            } for config in configs]
        })
    except Exception as e:
        current_app.logger.error(f"Error obteniendo configuraciones: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/configuraciones', methods=['POST'])
@login_required
def guardar_configuraciones():
    """Guarda o actualiza configuraciones contables"""
    try:
        datos = request.get_json()
        
        for clave, valor in datos.items():
            config = ConfiguracionContable.query.filter_by(clave=clave).first()
            if config:
                config.valor = valor
            else:
                config = ConfiguracionContable(
                    clave=clave,
                    valor=valor,
                    descripcion=f'Configuración: {clave}'
                )
                db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configuraciones guardadas correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error guardando configuraciones: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# También necesitaremos agregar el modelo
class ConfiguracionContable(db.Model):
    """Modelo para las configuraciones contables"""
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.String(255))
    descripcion = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, default=db.func.now())
    fecha_modificacion = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<ConfiguracionContable {self.clave}>'

# Agregar estas rutas al archivo routes.py en la carpeta de contabilidad

@contabilidad_bp.route('/flujo_caja')
@login_required
def ver_flujo_caja():
    """Vista principal del flujo de caja"""
    return render_template('contabilidad/flujo_caja.html')

@contabilidad_bp.route('/api/flujo_caja/generar', methods=['GET'])
@login_required
def generar_flujo_caja():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({
                'success': False,
                'error': 'Se requieren fechas de inicio y fin'
            }), 400

        # Convertir fechas
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')

        # Obtener ingresos
        ingresos = db.session.query(
            FlujoCaja.concepto,
            db.func.sum(FlujoCaja.monto).label('total')
        ).filter(
            FlujoCaja.fecha.between(fecha_inicio, fecha_fin),
            FlujoCaja.tipo == 'INGRESO',
            FlujoCaja.estado == 'Aprobado'
        ).group_by(
            FlujoCaja.concepto
        ).all()

        # Obtener egresos
        egresos = db.session.query(
            FlujoCaja.concepto,
            db.func.sum(FlujoCaja.monto).label('total')
        ).filter(
            FlujoCaja.fecha.between(fecha_inicio, fecha_fin),
            FlujoCaja.tipo == 'EGRESO',
            FlujoCaja.estado == 'Aprobado'
        ).group_by(
            FlujoCaja.concepto
        ).all()

        # Calcular saldo inicial (todo antes de fecha_inicio)
        saldo_inicial = db.session.query(
            db.func.sum(
                db.case(
                    (FlujoCaja.tipo == 'INGRESO', FlujoCaja.monto),
                    (FlujoCaja.tipo == 'EGRESO', -FlujoCaja.monto),
                    else_=0
                )
            )
        ).filter(
            FlujoCaja.fecha < fecha_inicio,
            FlujoCaja.estado == 'Aprobado'
        ).scalar() or 0

        # Procesar datos
        total_ingresos = sum(float(ingreso.total) for ingreso in ingresos)
        total_egresos = sum(float(egreso.total) for egreso in egresos)
        saldo_final = float(saldo_inicial) + total_ingresos - total_egresos

        return jsonify({
            'success': True,
            'data': {
                'ingresos': [{
                    'concepto': ingreso.concepto,
                    'monto': float(ingreso.total)
                } for ingreso in ingresos],
                'egresos': [{
                    'concepto': egreso.concepto,
                    'monto': float(egreso.total)
                } for egreso in egresos],
                'saldo_inicial': float(saldo_inicial),
                'saldo_final': saldo_final,
                'total_ingresos': total_ingresos,
                'total_egresos': total_egresos,
                'periodo': {
                    'inicio': fecha_inicio.strftime('%Y-%m-%d'),
                    'fin': fecha_fin.strftime('%Y-%m-%d')
                }
            }
        })

    except Exception as e:
        logger.error(f"Error generando flujo de caja: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/flujo_caja/movimientos', methods=['POST'])
@login_required
def registrar_movimiento_caja():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['concepto', 'tipo', 'monto', 'fecha']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'El campo {field} es requerido'
                }), 400

        # Crear nuevo movimiento
        nuevo_movimiento = FlujoCaja(
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d'),
            concepto=data['concepto'],
            tipo=data['tipo'],
            monto=data['monto'],
            cuenta_id=data.get('cuenta_id'),
            referencia=data.get('referencia'),
            descripcion=data.get('descripcion'),
            estado='Pendiente',
            creado_por=current_user.id
        )
        
        db.session.add(nuevo_movimiento)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Movimiento registrado exitosamente',
            'movimiento': nuevo_movimiento.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registrando movimiento de caja: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/flujo_caja/movimientos/<int:movimiento_id>', methods=['PUT'])
@login_required
def actualizar_movimiento_caja(movimiento_id):
    try:
        movimiento = FlujoCaja.query.get_or_404(movimiento_id)
        data = request.get_json()

        # Actualizar campos permitidos
        allowed_fields = ['concepto', 'tipo', 'monto', 'fecha', 'cuenta_id', 
                         'referencia', 'descripcion', 'estado']
        
        for field in allowed_fields:
            if field in data:
                if field == 'fecha':
                    setattr(movimiento, field, datetime.strptime(data[field], '%Y-%m-%d'))
                else:
                    setattr(movimiento, field, data[field])

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Movimiento actualizado exitosamente',
            'movimiento': movimiento.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error actualizando movimiento de caja: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500