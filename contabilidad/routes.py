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
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

        # Crear la cuenta con los campos permitidos
        cuenta_data = {
            'numero_cuenta': data.get('numero_cuenta'),
            'nombre': data.get('nombre'),
            'origen': data.get('origen'),
            'categoria': data.get('categoria'),
            'nivel': data.get('nivel'),
            'padre_id': data.get('padre_id'),
            'tipo': data.get('tipo'),
            'grupo': data.get('grupo'),
            'descripcion': data.get('descripcion'),
            'estatus': data.get('estatus', 'Activo'),
            'flujo_efectivo': data.get('flujo_efectivo'),
            'corriente': data.get('corriente', False),
            'balance_general': data.get('balance_general', False)
        }

        cuenta = ContabilidadCuenta(**cuenta_data)
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
@login_required
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
        
        return jsonify({
            'success': True,
            'cuentas': [cuenta.to_dict() for cuenta in cuentas]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contabilidad_bp.route('/api/cargar-catalogo', methods=['POST'])
def cargar_catalogo():
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró el archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file, skiprows=3)
            df.columns = ['numero_cuenta', 'nombre', 'origen', 'categoria']
            df = df.dropna(subset=['numero_cuenta', 'nombre'])
            
            cuentas_creadas = 0
            cuentas_actualizadas = 0
            errores = []

            for _, row in df.iterrows():
                try:
                    numero = str(row['numero_cuenta']).strip()
                    nombre = str(row['nombre']).strip()
                    origen = str(row['origen']).strip() if not pd.isna(row['origen']) else None
                    categoria = str(row['categoria']).strip() if not pd.isna(row['categoria']) else None

                    cuenta = ContabilidadCuenta.query.filter_by(numero_cuenta=numero).first()
                    
                    if cuenta:
                        cuenta.nombre = nombre
                        cuenta.origen = origen
                        cuenta.categoria = categoria
                        cuenta.calcular_nivel_y_padre()
                        cuentas_actualizadas += 1
                    else:
                        cuenta = ContabilidadCuenta(
                            numero_cuenta=numero,
                            nombre=nombre,
                            origen=origen,
                            categoria=categoria
                        )
                        cuenta.calcular_nivel_y_padre()
                        db.session.add(cuenta)
                        cuentas_creadas += 1

                except Exception as e:
                    errores.append(f"Error en cuenta {numero}: {str(e)}")
                    continue

            db.session.commit()
            
            mensaje = f"Proceso completado. Cuentas creadas: {cuentas_creadas}, actualizadas: {cuentas_actualizadas}"
            if errores:
                mensaje += f"\nErrores encontrados: {len(errores)}"
            
            return jsonify({
                'success': True,
                'message': mensaje,
                'errores': errores
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f"Error al procesar el archivo: {str(e)}"
            }), 400

    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@contabilidad_bp.route('/api/descargar-catalogo', methods=['GET'])
def descargar_catalogo():
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Catálogo de Cuentas"

        # Encabezado
        ws.merge_cells('A1:D1')
        ws['A1'] = 'EMPRESA:_____________________________________'
        ws.merge_cells('A2:D2')
        ws['A2'] = 'CATALOGO DE CUENTA'
        
        # Columnas
        ws['A4'] = 'NO. CUENTA'
        ws['B4'] = 'NOMBRE DE LA CUENTA'
        ws['C4'] = 'ORIGEN'
        ws['D4'] = 'CATEGORIA'

        # Datos
        cuentas = ContabilidadCuenta.query.order_by(ContabilidadCuenta.numero_cuenta).all()
        row = 5
        for cuenta in cuentas:
            ws[f'A{row}'] = cuenta.numero_cuenta
            ws[f'B{row}'] = cuenta.nombre
            ws[f'C{row}'] = cuenta.origen
            ws[f'D{row}'] = cuenta.categoria
            row += 1

        # Formato
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15

        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='catalogo_cuentas.xlsx'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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