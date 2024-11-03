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

def extract_cedula_info(texto_ocr):
    cedula_pattern = r"(?:CEDULADEIDENTIDAD(?:\s*Y\s*ELECTORAL)?|CEDULA\s*DE\s*IDENTIDAD(?:\s*Y\s*ELECTORAL)?)\s*([\d-]+)"
    nombre_pattern = r"FECHA(?:\s*DE)?\s*EXPIRACION\s*.*?\n((?:[A-Z]+\s*)+)$"
    lugar_nacimiento_pattern = r"LUGAR(?:\s*DE)?\s*NACIMIENTO\s*(.+?)(?:\n|$)"
    fecha_nacimiento_pattern = r"FECHA(?:\s*DE)?\s*NACIMIENTO:?\s*(\d{2}\w+\d{4})"

    cedula_match = re.search(cedula_pattern, texto_ocr, re.IGNORECASE | re.MULTILINE)
    nombre_match = re.search(nombre_pattern, texto_ocr, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    lugar_nacimiento_match = re.search(lugar_nacimiento_pattern, texto_ocr, re.IGNORECASE)
    fecha_nacimiento_match = re.search(fecha_nacimiento_pattern, texto_ocr, re.IGNORECASE)

    if cedula_match and nombre_match and lugar_nacimiento_match and fecha_nacimiento_match:
        fecha_nacimiento = format_date(fecha_nacimiento_match.group(1).strip())
        return {
            "CEDULADEIDENTIDAD": cedula_match.group(1).strip(),
            "NOMBRE": clean_name(nombre_match.group(1)),
            "LUGAR DE NACIMIENTO": lugar_nacimiento_match.group(1).strip(),
            "FECHA DE NACIMIENTO": fecha_nacimiento
        }
    return None

def extract_factura_info(texto_ocr):
    """
    Extrae información específica de una factura a partir del texto OCR.
    """
    logger.debug(f"Texto OCR recibido:\n{texto_ocr}")
    
    patterns = {
        'NCF': r"NCF\.\.\s*(.*?)(?:\n|$)",
        'Fecha': r"Fecha:\s*(.*?)(?:\n|$)",
        'RNC': r"RNC:\s*(.*?)(?:\n|$)",
        'TOTAL': r"TOTAL:\s*\$(.*?)(?:\n|$)",
        'Itbis': r"Itbis:\s*(.*?)(?:\n|$)"
    }
    
    result = {}
    try:
        for key, pattern in patterns.items():
            match = re.search(pattern, texto_ocr, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                logger.debug(f"Encontrado {key}: {value}")
                
                # Procesar valores numéricos
                if key in ['TOTAL', 'Itbis']:
                    try:
                        # Remover el símbolo $ si existe y las comas
                        value = value.replace('$', '').replace(',', '')
                        value = float(value)
                        logger.debug(f"Valor numérico convertido para {key}: {value}")
                    except ValueError as ve:
                        logger.warning(f"Error convirtiendo valor numérico para {key}: {value}")
                        logger.warning(str(ve))
                        continue
                result[key] = value
            else:
                logger.warning(f"No se encontró coincidencia para {key}")
        
        # Validar campos requeridos
        required_fields = {'NCF', 'Fecha', 'RNC'}
        found_fields = set(result.keys())
        logger.debug(f"Campos encontrados: {found_fields}")
        
        if all(field in result for field in required_fields):
            logger.info("Todos los campos requeridos fueron encontrados")
            return result
        else:
            missing_fields = required_fields - found_fields
            logger.error(f"Faltan campos requeridos: {missing_fields}")
            return None
            
    except Exception as e:
        logger.error(f"Error procesando texto OCR: {str(e)}")
        logger.error(traceback.format_exc())
        return None

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
    try:
        logger.debug("Iniciando procesamiento OCR")
        
        if 'image' not in request.files:
            logger.error("No se encontró archivo en la solicitud")
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files['image']
        if file.filename == '':
            logger.error("Nombre de archivo vacío")
            return jsonify({"error": "No selected file"}), 400
        
        logger.debug(f"Procesando archivo: {file.filename}")
        
        valid_extensions = {'jpg', 'jpeg', 'png'}
        file_extension = file.filename.rsplit('.', 1)[-1].lower()
        
        if file_extension not in valid_extensions:
            logger.error(f"Extensión de archivo inválida: {file_extension}")
            return jsonify({"error": "Invalid file type"}), 400

        # Leer y procesar la imagen
        image_stream = file.read()
        image_array = np.frombuffer(image_stream, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("No se pudo decodificar la imagen")
            return jsonify({"error": "Could not decode image"}), 400

        # Preprocesamiento
        logger.debug("Iniciando preprocesamiento de imagen")
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Mejora de contraste
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

        # OCR
        logger.debug("Iniciando proceso OCR")
        resultado_ocr = ocr.ocr(enhanced, cls=True)
        
        if not resultado_ocr or not resultado_ocr[0]:
            logger.error("No se detectó texto en la imagen")
            return jsonify({
                "error": "No text detected in image",
                "details": "El OCR no pudo detectar texto en la imagen"
            }), 400

        # Extraer texto
        texto_ocr = "\n".join([line[1][0] for line in resultado_ocr[0] if line])
        logger.debug(f"Texto extraído por OCR:\n{texto_ocr}")

        # Procesar información
        factura_info = extract_factura_info(texto_ocr)
        logger.debug(f"Información extraída: {factura_info}")
        
        if not factura_info:
            logger.error("No se pudo extraer la información requerida de la factura")
            return jsonify({
                "error": "No se pudo extraer la información requerida",
                "texto_detectado": texto_ocr,
                "details": "No se encontraron todos los campos requeridos"
            }), 400

        # Preparar respuesta
        formulario606_data = {
            'fecha': factura_info.get('Fecha', ''),
            'ncf': factura_info.get('NCF', ''),
            'rnc_cedula': factura_info.get('RNC', ''),
            'monto': factura_info.get('TOTAL', 0.0),
            'itbis': factura_info.get('Itbis', 0.0)
        }

        logger.debug(f"Datos extraídos exitosamente: {formulario606_data}")
        
        return jsonify({
            "success": True,
            "ocr_data": formulario606_data,
            "classification": "Archivo válido: Esto es una factura",
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
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500


# Ensure the temp directory exists
os.makedirs('temp', exist_ok=True)