from flask import render_template, request, jsonify, abort, send_file
from . import contabilidad_bp
from .models import (ContabilidadCuenta, AsientoDiario, MayorGeneral, 
                    BalanzaComprobacion, EstadoResultados, BalanceGeneral, 
                    Configuraciones, FlujoCaja)
from app import db
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from io import BytesIO
import os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
import logging

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
        
        query = ContabilidadCuenta.query
        
        if numero:
            query = query.filter(ContabilidadCuenta.numero_cuenta.ilike(f'%{numero}%'))
        if nombre:
            query = query.filter(ContabilidadCuenta.nombre.ilike(f'%{nombre}%'))
        if categoria:
            query = query.filter(ContabilidadCuenta.categoria == categoria)
            
        cuentas = query.order_by(ContabilidadCuenta.numero_cuenta).all()
        
        cuentas_data = [{
            'id': cuenta.id,
            'numero_cuenta': cuenta.numero_cuenta,
            'nombre': cuenta.nombre,
            'padre_id': cuenta.padre_id,
            'tipo': cuenta.tipo or '',
            'categoria': cuenta.categoria,
            'grupo': cuenta.grupo or '',
        } for cuenta in cuentas]
        
        return jsonify({
            'success': True,
            'cuentas': cuentas_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@contabilidad_bp.route('/api/mayor-general', methods=['GET'])
def obtener_mayor_general():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({
                'success': False,
                'error': 'Se requieren fechas de inicio y fin'
            }), 400
        
        fecha_inicio = format_date(fecha_inicio)
        fecha_fin = format_date(fecha_fin)
        
        mayor_general = MayorGeneral.query.filter(
            MayorGeneral.fecha.between(fecha_inicio, fecha_fin)
        ).order_by(MayorGeneral.cuenta_id, MayorGeneral.fecha).all()
        
        return jsonify({
            'success': True,
            'mayor_general': [entrada.to_dict() for entrada in mayor_general]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/balanza-comprobacion', methods=['GET'])
def obtener_balanza_comprobacion():
    try:
        fecha = request.args.get('fecha')
        
        if not fecha:
            return jsonify({
                'success': False,
                'error': 'Se requiere una fecha'
            }), 400
        
        fecha = format_date(fecha)
        
        balanza = BalanzaComprobacion.query.filter_by(fecha=fecha).all()
        
        return jsonify({
            'success': True,
            'balanza_comprobacion': [entrada.to_dict() for entrada in balanza]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/estado-resultados', methods=['GET'])
def obtener_estado_resultados():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({
                'success': False,
                'error': 'Se requieren fechas de inicio y fin'
            }), 400
        
        fecha_inicio = format_date(fecha_inicio)
        fecha_fin = format_date(fecha_fin)
        
        estado_resultados = EstadoResultados.query.filter(
            EstadoResultados.fecha.between(fecha_inicio, fecha_fin)
        ).order_by(EstadoResultados.fecha).all()
        
        return jsonify({
            'success': True,
            'estado_resultados': [entrada.to_dict() for entrada in estado_resultados]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/balance-general', methods=['GET'])
def obtener_balance_general():
    try:
        fecha = request.args.get('fecha')
        
        if not fecha:
            return jsonify({
                'success': False,
                'error': 'Se requiere una fecha'
            }), 400
        
        fecha = format_date(fecha)
        
        balance = BalanceGeneral.query.filter_by(fecha=fecha).first()
        
        if not balance:
            return jsonify({
                'success': False,
                'error': 'No se encontró un balance general para la fecha especificada'
            }), 404
        
        return jsonify({
            'success': True,
            'balance_general': balance.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/configuraciones', methods=['GET', 'POST'])
@login_required
def manejar_configuraciones():
    if request.method == 'GET':
        try:
            configuraciones = Configuraciones.query.first()
            return jsonify({
                'success': True,
                'configuraciones': configuraciones.to_dict() if configuraciones else {}
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    elif request.method == 'POST':
        try:
            data = request.json
            configuraciones = Configuraciones.query.first()
            
            if not configuraciones:
                configuraciones = Configuraciones()
                db.session.add(configuraciones)
            
            for key, value in data.items():
                setattr(configuraciones, key, value)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Configuraciones actualizadas exitosamente'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

@contabilidad_bp.route('/api/flujo-caja', methods=['GET'])
def obtener_flujo_caja():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({
                'success': False,
                'error': 'Se requieren fechas de inicio y fin'
            }), 400
        
        fecha_inicio = format_date(fecha_inicio)
        fecha_fin = format_date(fecha_fin)
        
        flujo_caja = FlujoCaja.query.filter(
            FlujoCaja.fecha.between(fecha_inicio, fecha_fin)
        ).order_by(FlujoCaja.fecha).all()
        
        return jsonify({
            'success': True,
            'flujo_caja': [entrada.to_dict() for entrada in flujo_caja]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500