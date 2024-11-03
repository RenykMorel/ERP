from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from .models import Formulario606, Formulario607, ReporteIT1, ImpuestoRenta, SerieFiscal, ConfiguracionesImpuestos
from datetime import datetime
import logging
import os
import re
from paddleocr import PaddleOCR
from werkzeug.utils import secure_filename
import traceback 
import numpy as np
import cv2

impuestos_bp = Blueprint('impuestos', __name__, url_prefix='/impuestos')

logger = logging.getLogger(__name__)

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='es')

# OCR helper functions
def clean_name(name):
    return ' '.join(name.split())

def format_date(date):
    date = re.sub(r'\s+', '', date)
    if len(date) >= 8:
        day, month, year = date[:2], date[2:-4], date[-4:]
        return f"{day} {month} {year}"
    return date


def extract_factura_info(texto_ocr):
    """
    Extrae información específica de una factura con procesamiento línea por línea mejorado.
    """
    logger.debug("=== INICIO DE PROCESAMIENTO DE FACTURA ===")
    logger.debug(f"Texto OCR recibido:\n{texto_ocr}")
    
    result = {}
    lines = texto_ocr.split('\n')
    
    # Buscar NCF
    for i, line in enumerate(lines):
        # NCF: Buscar en la línea actual y la siguiente
        if 'NCF' in line:
            for j in range(i, min(i + 2, len(lines))):
                if lines[j].strip().startswith('B'):
                    result['NCF'] = lines[j].strip()
                    logger.debug(f"NCF encontrado: {result['NCF']}")
                    break
        
        # RNC: Buscar en cualquier línea que contenga "RNC"
        if 'RNC' in line and 'n/a' not in line.lower():
            rnc_matches = re.findall(r'\d{9,11}', line)
            if rnc_matches:
                result['RNC'] = rnc_matches[0]
                logger.debug(f"RNC encontrado: {result['RNC']}")
        
        # Fecha: Buscar en la línea actual
        if 'Fecha:' in line or (i > 0 and 'Fecha:' in lines[i-1]):
            fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
            if fecha_match:
                result['Fecha'] = fecha_match.group(1)
                logger.debug(f"Fecha encontrada: {result['Fecha']}")
        
        # TOTAL: Buscar al final del documento
        if 'TOTAL:' in line or 'TOTAL' in line:
            total_match = re.search(r'\$\s*(\d+\.\d{2})', line)
            if total_match:
                try:
                    result['TOTAL'] = float(total_match.group(1))
                    logger.debug(f"TOTAL encontrado: {result['TOTAL']}")
                except ValueError:
                    logger.warning(f"Error convirtiendo TOTAL: {total_match.group(1)}")
        
        # Itbis: Buscar en cualquier línea
        if 'Itbis:' in line:
            itbis_match = re.search(r'(\d+\.\d{2})', line)
            if itbis_match:
                try:
                    result['Itbis'] = float(itbis_match.group(1))
                    logger.debug(f"Itbis encontrado: {result['Itbis']}")
                except ValueError:
                    logger.warning(f"Error convirtiendo Itbis: {itbis_match.group(1)}")

    # Segunda pasada para campos que podrían estar en formatos alternativos
    if 'TOTAL' not in result:
        for line in lines:
            if '$' in line and not any(key in line.upper() for key in ['SUBTOTAL', 'ITBIS']):
                total_match = re.search(r'\$\s*(\d+\.\d{2})', line)
                if total_match:
                    try:
                        result['TOTAL'] = float(total_match.group(1))
                        logger.debug(f"TOTAL encontrado (segunda pasada): {result['TOTAL']}")
                    except ValueError:
                        continue

    if 'RNC' not in result:
        # Buscar cualquier número de 9-11 dígitos después de la palabra RNC
        for line in lines:
            if 'RNC' in line and 'n/a' not in line.lower():
                rnc_value = ''.join(filter(str.isdigit, line))
                if len(rnc_value) in [9, 10, 11]:
                    result['RNC'] = rnc_value
                    logger.debug(f"RNC encontrado (segunda pasada): {result['RNC']}")
                    break

    # Validación y logging de resultados
    logger.debug("=== RESULTADOS ENCONTRADOS ===")
    for key, value in result.items():
        logger.debug(f"{key}: {value}")

    # Verificar campos requeridos
    required_fields = {'NCF', 'Fecha', 'RNC'}
    found_fields = set(result.keys())
    missing_fields = required_fields - found_fields
    
    if missing_fields:
        logger.error(f"Faltan campos requeridos: {missing_fields}")
        return None
    
    return result

@impuestos_bp.route('/formulario606')
@login_required
def formulario606():
    try:
        registros = Formulario606.query.all()
        return render_template('impuestos/formulario606.html', registros=registros)
    except Exception as e:
        logger.error(f"Error al cargar el Formulario 606: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/formulario606/crear', methods=['GET', 'POST'])
@login_required
def crear_formulario606():
    if request.method == 'POST':
        try:
            nuevo_registro = Formulario606(
                fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                rnc_cedula=request.form['rnc_cedula'],
                tipo_bienes_servicios=request.form['tipo_bienes_servicios'],
                ncf=request.form['ncf'],
                monto=float(request.form['monto'])
            )
            db.session.add(nuevo_registro)
            db.session.commit()
            flash('Registro de Formulario 606 creado exitosamente', 'success')
            return redirect(url_for('impuestos.formulario606'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear registro de Formulario 606: {str(e)}")
            flash('Error al crear el registro', 'error')
    return render_template('impuestos/crear_formulario606.html')

@impuestos_bp.route('/formulario607')
@login_required
def formulario607():
    try:
        registros = Formulario607.query.all()
        return render_template('impuestos/formulario607.html', registros=registros)
    except Exception as e:
        logger.error(f"Error al cargar el Formulario 607: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/formulario607/crear', methods=['GET', 'POST'])
@login_required
def crear_formulario607():
    if request.method == 'POST':
        try:
            nuevo_registro = Formulario607(
                fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                rnc_cedula=request.form['rnc_cedula'],
                tipo_ingreso=request.form['tipo_ingreso'],
                ncf=request.form['ncf'],
                monto=float(request.form['monto'])
            )
            db.session.add(nuevo_registro)
            db.session.commit()
            flash('Registro de Formulario 607 creado exitosamente', 'success')
            return redirect(url_for('impuestos.formulario607'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear registro de Formulario 607: {str(e)}")
            flash('Error al crear el registro', 'error')
    return render_template('impuestos/crear_formulario607.html')

@impuestos_bp.route('/reporte-it1')
@login_required
def reporte_it1():
    try:
        reportes = ReporteIT1.query.all()
        return render_template('impuestos/reporte_it1.html', reportes=reportes)
    except Exception as e:
        logger.error(f"Error al cargar el Reporte IT1: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/reporte-it1/crear', methods=['GET', 'POST'])
@login_required
def crear_reporte_it1():
    if request.method == 'POST':
        try:
            nuevo_reporte = ReporteIT1(
                periodo=request.form['periodo'],
                total_ingresos=float(request.form['total_ingresos']),
                total_gastos=float(request.form['total_gastos']),
                impuesto_pagado=float(request.form['impuesto_pagado'])
            )
            db.session.add(nuevo_reporte)
            db.session.commit()
            flash('Reporte IT1 creado exitosamente', 'success')
            return redirect(url_for('impuestos.reporte_it1'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear Reporte IT1: {str(e)}")
            flash('Error al crear el reporte', 'error')
    return render_template('impuestos/crear_reporte_it1.html')

@impuestos_bp.route('/ir17')
@login_required
def ir17():
    try:
        declaraciones = ImpuestoRenta.query.all()
        return render_template('impuestos/ir17.html', declaraciones=declaraciones)
    except Exception as e:
        logger.error(f"Error al cargar el IR17: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/ir17/crear', methods=['GET', 'POST'])
@login_required
def crear_ir17():
    if request.method == 'POST':
        try:
            nueva_declaracion = ImpuestoRenta(
                ano_fiscal=int(request.form['ano_fiscal']),
                ingresos_totales=float(request.form['ingresos_totales']),
                gastos_deducibles=float(request.form['gastos_deducibles']),
                renta_neta_imponible=float(request.form['renta_neta_imponible']),
                impuesto_liquidado=float(request.form['impuesto_liquidado'])
            )
            db.session.add(nueva_declaracion)
            db.session.commit()
            flash('Declaración IR17 creada exitosamente', 'success')
            return redirect(url_for('impuestos.ir17'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear declaración IR17: {str(e)}")
            flash('Error al crear la declaración', 'error')
    return render_template('impuestos/crear_ir17.html')

@impuestos_bp.route('/serie-fiscal')
@login_required
def serie_fiscal():
    try:
        series = SerieFiscal.query.all()
        return render_template('impuestos/serie_fiscal.html', series=series)
    except Exception as e:
        logger.error(f"Error al cargar las Series Fiscales: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/serie-fiscal/crear', methods=['GET', 'POST'])
@login_required
def crear_serie_fiscal():
    if request.method == 'POST':
        try:
            nueva_serie = SerieFiscal(
                serie=request.form['serie'],
                tipo_comprobante=request.form['tipo_comprobante'],
                fecha_vencimiento=datetime.strptime(request.form['fecha_vencimiento'], '%Y-%m-%d').date(),
                secuencia_desde=int(request.form['secuencia_desde']),
                secuencia_hasta=int(request.form['secuencia_hasta'])
            )
            db.session.add(nueva_serie)
            db.session.commit()
            flash('Serie Fiscal creada exitosamente', 'success')
            return redirect(url_for('impuestos.serie_fiscal'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear Serie Fiscal: {str(e)}")
            flash('Error al crear la Serie Fiscal', 'error')
    return render_template('impuestos/crear_serie_fiscal.html')

@impuestos_bp.route('/configuraciones')
@login_required
def configuraciones():
    try:
        config = ConfiguracionesImpuestos.query.first()
        if not config:
            config = ConfiguracionesImpuestos()
            db.session.add(config)
            db.session.commit()
        return render_template('impuestos/configuraciones.html', configuraciones=config)
    except Exception as e:
        logger.error(f"Error al cargar las Configuraciones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/configuraciones/guardar', methods=['POST'])
@login_required
def guardar_configuraciones():
    try:
        config = ConfiguracionesImpuestos.query.first()
        if not config:
            config = ConfiguracionesImpuestos()

        config.tasa_itbis = float(request.form['tasa_itbis'])
        config.tasa_isr_personas = float(request.form['tasa_isr_personas'])
        config.tasa_isr_empresas = float(request.form['tasa_isr_empresas'])
        config.limite_facturacion_606 = float(request.form['limite_facturacion_606'])

        db.session.add(config)
        db.session.commit()

        flash('Configuraciones guardadas exitosamente', 'success')
        return redirect(url_for('impuestos.configuraciones'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al guardar las Configuraciones: {str(e)}")
        flash('Error al guardar las configuraciones', 'error')
        return redirect(url_for('impuestos.configuraciones'))

# API endpoints for frontend interaction

@impuestos_bp.route('/api/formulario606', methods=['GET'])
@login_required
def api_formulario606():
    try:
        registros = Formulario606.query.all()
        return jsonify([registro.to_dict() for registro in registros])
    except Exception as e:
        logger.error(f"Error al obtener registros de Formulario 606: {str(e)}")
        return jsonify({"error": str(e)}), 500

@impuestos_bp.route('/api/formulario606', methods=['POST'])
@login_required
def api_crear_formulario606():
    try:
        data = request.json
        nuevo_registro = Formulario606(
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
            rnc_cedula=data['rnc_cedula'],
            tipo_bienes_servicios=data['tipo_bienes_servicios'],
            ncf=data['ncf'],
            monto=float(data['monto'])
        )
        db.session.add(nuevo_registro)
        db.session.commit()
        return jsonify({"success": True, "message": "Registro creado exitosamente"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear registro de Formulario 606: {str(e)}")
        return jsonify({"error": str(e)}), 400

@impuestos_bp.route('/api/formulario606/<int:id>', methods=['PUT'])
@login_required
def api_actualizar_formulario606(id):
    try:
        registro = Formulario606.query.get_or_404(id)
        data = request.json
        registro.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        registro.rnc_cedula = data['rnc_cedula']
        registro.tipo_bienes_servicios = data['tipo_bienes_servicios']
        registro.ncf = data['ncf']
        registro.monto =   float(data['monto'])
        db.session.commit()
        return jsonify({"success": True, "message": "Registro actualizado exitosamente"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar registro de Formulario 606: {str(e)}")
        return jsonify({"error": str(e)}), 400

@impuestos_bp.route('/api/formulario606/<int:id>', methods=['DELETE'])
@login_required
def api_eliminar_formulario606(id):
    try:
        registro = Formulario606.query.get_or_404(id)
        db.session.delete(registro)
        db.session.commit()
        return jsonify({"success": True, "message": "Registro eliminado exitosamente"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar registro de Formulario 606: {str(e)}")
        return jsonify({"error": str(e)}), 400

@impuestos_bp.route('/api/ocr', methods=['POST'])
@login_required
def api_ocr():
    """
    Endpoint para procesar imágenes de facturas usando OCR.
    """
    try:
        logger.debug("=== INICIANDO PROCESO OCR ===")
        
        if 'image' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Leer y procesar la imagen
        image_stream = file.read()
        image_array = np.frombuffer(image_stream, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({"error": "Could not decode image"}), 400

        # Preprocesamiento
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Mejora de contraste
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

        # OCR con logging detallado
        logger.debug("Ejecutando OCR...")
        resultado_ocr = ocr.ocr(enhanced, cls=True)
        
        if not resultado_ocr or not resultado_ocr[0]:
            return jsonify({"error": "No text detected in image"}), 400

        # Mostrar cada línea detectada
        logger.debug("=== TEXTO DETECTADO POR OCR ===")
        texto_ocr = ""
        for i, line in enumerate(resultado_ocr[0]):
            if line:
                texto_detectado = line[1][0]
                confidence = line[1][1]
                logger.debug(f"Línea {i+1}: '{texto_detectado}' (Confianza: {confidence})")
                texto_ocr += texto_detectado + "\n"

        # Procesar información
        factura_info = extract_factura_info(texto_ocr)
        
        if not factura_info:
            return jsonify({
                "error": "No se pudo extraer la información requerida",
                "debug_info": {
                    "texto_detectado": texto_ocr
                }
            }), 400

        formulario606_data = {
            'fecha': factura_info.get('Fecha', ''),
            'ncf': factura_info.get('NCF', ''),
            'rnc_cedula': factura_info.get('RNC', ''),
            'monto': factura_info.get('TOTAL', 0.0),
            'itbis': factura_info.get('Itbis', 0.0)
        }

        return jsonify({
            "success": True,
            "ocr_data": formulario606_data,
            "debug_info": {
                "texto_detectado": texto_ocr,
                "campos_encontrados": list(factura_info.keys())
            }
        })

    except Exception as e:
        logger.error(f"Error en procesamiento OCR: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": "OCR processing failed",
            "details": str(e)
        }), 500



# Ensure the temp directory exists
os.makedirs('temp', exist_ok=True)