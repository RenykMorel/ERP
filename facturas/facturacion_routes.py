from flask import Blueprint, request, jsonify, render_template, current_app, make_response, render_template_string
from flask_login import login_required, current_user
import pdfkit
import os
import json
from flask import jsonify, request
import traceback
import numpy as np
from .facturas_models import (
    Facturacion, PreFactura, NotaCredito, NotaDebito, 
    Cliente, TiendaFactura, ItemPreFactura, Vendedor, FacturaTemplate
)
from common.models import (
    ItemFactura, ItemPreFactura, MovimientoInventario
)
from inventario.inventario_models import InventarioItem
from extensions import db
from . import facturacion_bp
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy import text, func
from .facturas_models import ItemPendiente, CodigoAutorizacion, InvoiceLayoutProcessor
from .helpers import (
    # Funciones de plantilla y formateo
    generate_default_template,
    generate_items_html,
    format_currency,
    
    # Funciones de análisis de clientes
    get_productos_frecuentes,
    get_metodos_pago,
    calculate_promedio,
    get_frecuencia_compra,
    get_productos_preferidos,
    
    # Funciones de análisis de ventas
    get_ventas_por_hora,
    get_volumen_transacciones,
    get_ticket_promedio_metodo,
    get_ticket_promedio,
    get_horarios_preferidos,
    get_tasa_rechazo,
    
    # Funciones de análisis comparativo
    get_comparativa_metodos,
    get_comparativa_diaria,
    get_comparativa_semanal,
    get_comparativa_mensual,
    get_comparativa_anual,
    get_comparativa_categorias,
    
    # Funciones de análisis de productos
    get_top_productos,
    get_tendencia_mensual,
    calculate_margen,
    get_stock_categoria,
    get_top_clientes_categoria,
    get_ventas_por_categoria,
    
    # Funciones de predicción y tendencias
    predict_next_month,
    get_tendencias,
    get_patrones_diarios,
    get_patrones_semanales,
    get_patrones_mensuales,
    
    # Funciones de métricas financieras
    calculate_growth_rate,
    calculate_customer_return_rate,
    calculate_customer_lifetime_value,
    calculate_churn_rate,
    calculate_inventory_turnover,
    calculate_days_inventory,
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_average_cogs,
    
    # Funciones de inventario
    get_stockouts,
    get_metricas_inventario,
    
    # Funciones de vendedores
    calculate_tasa_conversion,
    get_productos_vendedor,
    get_clientes_vendedor,
    get_historico_vendedor,
    calculate_comisiones
)

config = pdfkit.configuration(wkhtmltopdf=r'C:\Users\el_re\OneDrive - Sendiu\Desktop\wkhtmltopdf\bin\wkhtmltopdf.exe')


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
    
@facturacion_bp.route('/api/templates/<int:template_id>/activate', methods=['POST'])
@login_required
def activate_template(template_id):
    try:
        # Obtener la plantilla
        template = FacturaTemplate.query.get_or_404(template_id)
        
        print(f"Activando plantilla {template_id} para tienda {template.tienda_id}")  # Debug log
        
        # Desactivar todas las plantillas para esa tienda
        FacturaTemplate.query.filter_by(
            tienda_id=template.tienda_id
        ).update({'activo': False})
        
        # Activar la plantilla seleccionada
        template.activo = True
        db.session.commit()
        
        print(f"Plantilla activada exitosamente")  # Debug log
        
        return jsonify({
            'success': True,
            'message': 'Plantilla activada correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error activando plantilla: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@facturacion_bp.route('/api/templates/<int:template_id>/preview')
@login_required
def template_preview(template_id):
    template = FacturaTemplate.query.get_or_404(template_id)
    return template.css_styles    
    
@facturacion_bp.route('/api/templates/generate', methods=['POST'])
@login_required
def generate_invoice_template():
    try:
        data = request.json
        print("Received data:", data)  # Debug log
        
        tienda_id = data.get('tienda_id')
        if not tienda_id:
            return jsonify({"error": "tienda_id es requerido"}), 400

        # Validate tienda exists
        tienda = TiendaFactura.query.get(tienda_id)
        if not tienda:
            return jsonify({"error": "Tienda no encontrada"}), 404

        processor = InvoiceLayoutProcessor()
        template = processor.generate_layout(tienda_id)

        # Deactivate previous templates
        FacturaTemplate.query.filter_by(
            tienda_id=tienda_id,
            activo=True
        ).update({'activo': False})

        db.session.add(template)
        db.session.commit()

        return jsonify({
            'success': True,
            'template_id': template.id,
            'template_preview': template.css_styles,
            'message': 'Nueva plantilla generada exitosamente'
        })

    except Exception as e:
        db.session.rollback()
        print("Error generating template:", str(e))  # Debug log
        return jsonify({'error': str(e)}), 500   
    
@facturacion_bp.route('/api/facturas/analisis', methods=['POST'])
@login_required
def analizar_facturas():
    try:
        data = request.get_json()
        today = datetime.now()
        fecha_inicio = datetime.strptime(data.get('fecha_inicio') or today.strftime('%Y-%m-%d'), '%Y-%m-%d')
        fecha_fin = datetime.strptime(data.get('fecha_fin') or today.strftime('%Y-%m-%d'), '%Y-%m-%d')

        facturas = Facturacion.query.filter(
            Facturacion.fecha.between(fecha_inicio, fecha_fin),
            Facturacion.estatus != 'anulada'
        ).all()

        total_facturas = len(facturas)
        total_ingresos = sum(float(f.total or 0) for f in facturas)

        return jsonify({
            "metadata": {
                "total_facturas": total_facturas,
                "periodo": {
                    "inicio": fecha_inicio.strftime('%Y-%m-%d'),
                    "fin": fecha_fin.strftime('%Y-%m-%d')
                }
            },
            "metricas": {
                "total_ingresos": total_ingresos,
                "ticket_promedio": total_ingresos / total_facturas if total_facturas > 0 else 0,
                "tasa_crecimiento": 0
            },
            "tendencias": {
                "ingresos_por_cliente": [],
                "ingresos_por_producto": [],
                "ingresos_por_mes": []
            },
            "patrones_sospechosos": [],
            "analisis_costos": {
                "oportunidades_ahorro": []
            }
        })

    except Exception as e:
        print(f"Error en analizar_facturas: {str(e)}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        print(f"Error en analizar_facturas: {str(e)}")  # Log para debugging
        return jsonify({"error": str(e)}), 500

def get_top_clientes(facturas):
    clientes = {}
    for factura in facturas:
        if factura.cliente:
            nombre = factura.cliente.nombre
            clientes[nombre] = clientes.get(nombre, 0) + float(factura.total or 0)
    return [{"cliente": k, "total": v} for k, v in sorted(clientes.items(), key=lambda x: x[1], reverse=True)][:5]

def get_analisis_temporal(facturas):
    ventas_por_mes = {}
    for factura in facturas:
        mes = factura.fecha.strftime('%Y-%m')
        ventas_por_mes[mes] = ventas_por_mes.get(mes, 0) + float(factura.total or 0)
    return [{"mes": k, "total": v} for k, v in sorted(ventas_por_mes.items())]

def calcular_tasa_crecimiento(ingresos_por_mes):
    if len(ingresos_por_mes) < 2:
        return 0
    
    meses = sorted(ingresos_por_mes.keys())
    primer_mes = ingresos_por_mes[meses[0]]
    ultimo_mes = ingresos_por_mes[meses[-1]]
    
    if primer_mes == 0:
        return 0
        
    return ((ultimo_mes - primer_mes) / primer_mes) * 100

# Funciones de análisis detalladas
def calcular_ingresos_por_cliente(facturas):
    ingresos = {}
    for factura in facturas:
        if factura.cliente:
            key = factura.cliente.nombre
            ingresos[key] = ingresos.get(key, 0) + factura.total
    return [{"cliente": k, "total": v} for k, v in sorted(ingresos.items(), key=lambda x: x[1], reverse=True)]

def calcular_ingresos_por_producto(facturas):
    ingresos = {}
    for factura in facturas:
        for item in factura.items:
            if item.item:
                key = item.item.nombre
                ingresos[key] = ingresos.get(key, 0) + (item.cantidad * item.precio_unitario)
    return [{"producto": k, "total": v} for k, v in sorted(ingresos.items(), key=lambda x: x[1], reverse=True)]

def proyectar_flujo_caja(facturas):
    # Proyección por mes
    flujo = {}
    for factura in facturas:
        mes = factura.fecha.strftime('%Y-%m')
        flujo[mes] = flujo.get(mes, 0) + factura.total
    return [{"mes": k, "proyeccion": v} for k, v in sorted(flujo.items())]

def detectar_precios_anomalos(facturas):
    anomalias = []
    for factura in facturas:
        for item in factura.items:
            # Calcular estadísticas de precios para este producto
            precios_historicos = obtener_precios_historicos(item.item_id)
            if precios_historicos:
                promedio = sum(precios_historicos) / len(precios_historicos)
                desviacion = calcular_desviacion_estandar(precios_historicos)
                if abs(item.precio_unitario - promedio) > (2 * desviacion):
                    anomalias.append({
                        "factura_id": factura.id,
                        "item_id": item.item_id,
                        "precio": item.precio_unitario,
                        "promedio_historico": promedio,
                        "desviacion": desviacion
                    })
    return anomalias

def identificar_oportunidades_ahorro(facturas):
    oportunidades = []
    # Análisis de descuentos no aprovechados
    for factura in facturas:
        if factura.total > 10000 and not factura.descuento_monto:
            oportunidades.append({
                "tipo": "descuento_volumen",
                "factura_id": factura.id,
                "monto": factura.total,
                "ahorro_potencial": factura.total * 0.05
            })
    return oportunidades

def calcular_desviacion_estandar(valores):
    if not valores:
        return 0
    media = sum(valores) / len(valores)
    suma_cuadrados = sum((x - media) ** 2 for x in valores)
    return (suma_cuadrados / len(valores)) ** 0.5

def obtener_precios_historicos(item_id):
    # Obtener historial de precios de los últimos 6 meses
    fecha_limite = datetime.now() - timedelta(days=180)
    items = ItemFactura.query.join(Facturacion).filter(
        ItemFactura.item_id == item_id,
        Facturacion.fecha >= fecha_limite
    ).all()
    return [item.precio_unitario for item in items]    

    
@facturacion_bp.route('/api/facturas/<int:factura_id>/print', methods=['GET'])
@login_required
def imprimir_factura(factura_id):
    try:
        factura = Facturacion.query.get_or_404(factura_id)
        
        template_id = request.args.get('template_id')
        template = None
        
        # Imprimir logs detallados
        print(f"Template ID solicitado: {template_id}")
        
        if template_id:
            template = FacturaTemplate.query.get(template_id)
            print(f"Plantilla encontrada por ID: {template.id if template else 'No encontrada'}")
            print(f"Contenido HTML de la plantilla: {template.html_template if template else 'N/A'}")
        
        if not template:
            template = FacturaTemplate.query.filter_by(
                tienda_id=factura.tienda_id,
                activo=True
            ).first()
            print(f"Plantilla encontrada por tienda: {template.id if template else 'No encontrada'}")
        
        if template:
            print("Usando plantilla personalizada")
            # Calcular totales para la factura
            subtotal = sum(item.cantidad * item.precio_unitario for item in factura.items)
            total_itbis = sum((item.cantidad * item.precio_unitario * item.itbis / 100) for item in factura.items if item.itbis)
            
            html_content = render_template_string(
                template.html_template,
                factura=factura,
                subtotal=subtotal,
                total_itbis=total_itbis,
                format_currency=format_currency
            )
        else:
            print("Usando plantilla por defecto")
            html_content = generate_default_template(factura)
            
        print("Generando PDF...")
        
        pdf = pdfkit.from_string(
            html_content, 
            False,
            options={
                'page-size': 'Letter',
                'encoding': 'UTF-8',
                'enable-local-file-access': None
            },
            configuration=config
        )
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=factura_{factura.numero}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error detallado al imprimir factura: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def generate_items_html(items):
    """Genera el HTML para los items de la factura"""
    items_html = ""
    for item in items:
        items_html += f"""
            <tr>
                <td>{item.item.nombre if item.item else 'N/A'}</td>
                <td>{item.cantidad}</td>
                <td>${format_currency(item.precio_unitario)}</td>
                <td>${format_currency(item.itbis)}</td>
                <td>${format_currency(item.cantidad * item.precio_unitario)}</td>
            </tr>
        """
    return items_html

def format_currency(amount):
    """Formatea cantidades monetarias"""
    return "{:,.2f}".format(float(amount or 0))
    
@facturacion_bp.route('/api/analyze-invoice-template', methods=['POST'])
@login_required
def analyze_invoice_template():
    try:
        data = request.json
        if not data or not data.get('image') or not data.get('tienda_id'):
            return jsonify({"error": "Imagen y tienda_id son requeridos"}), 400

        processor = InvoiceLayoutProcessor()
        template = processor.analyze_layout(data['image'], data['tienda_id'])

        # Desactivar templates anteriores
        FacturaTemplate.query.filter_by(
            tienda_id=data['tienda_id'],
            activo=True
        ).update({'activo': False})

        db.session.add(template)
        db.session.commit()

        return jsonify({
            'success': True,
            'template_id': template.id,
            'message': 'Plantilla procesada y guardada correctamente'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error al procesar plantilla: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@facturacion_bp.route('/api/templates/fix/<int:template_id>', methods=['POST'])
@login_required
def fix_template(template_id):
    try:
        template = FacturaTemplate.query.get_or_404(template_id)
        
        # Generar nuevo HTML para la plantilla
        processor = InvoiceLayoutProcessor()
        colors = {
            'primary': '#4a90e2',
            'secondary': '#5c6ac4',
            'text': '#333333',
            'border': '#dddddd'
        }
        template.html_template = processor._modern_layout(colors)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Plantilla actualizada correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500    
    
@facturacion_bp.route('/api/templates', methods=['GET'])
@login_required
def get_templates():
    templates = FacturaTemplate.query.all()
    return jsonify([{
        'id': t.id,
        'nombre': t.nombre,
        'fecha_creacion': t.fecha_creacion.isoformat()
    } for t in templates])    
    
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
    
@facturacion_bp.route('/api/reporte-ventas', methods=['GET'])
@login_required
def get_reporte_ventas():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        tipo_venta = request.args.get('tipo_venta')
        cliente_id = request.args.get('cliente')
        vendedor_id = request.args.get('vendedor')
        categoria_producto = request.args.get('categoria_producto')
        
        # Convertir fechas
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d') if fecha_inicio else None
        fecha_fin = datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S') if fecha_fin else None
        
        # Query base
        query = Facturacion.query.filter(Facturacion.estatus != 'anulada')
        
        # Aplicar filtros
        if fecha_inicio:
            query = query.filter(Facturacion.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Facturacion.fecha <= fecha_fin)
        if tipo_venta:
            query = query.filter(Facturacion.tipo == tipo_venta)
        if cliente_id:
            query = query.filter(Facturacion.cliente_id == cliente_id)
        if vendedor_id:
            query = query.filter(Facturacion.vendedor_id == vendedor_id)
            
        # Obtener facturas
        facturas = query.order_by(Facturacion.fecha.desc()).all()
        
        if not facturas:
            return jsonify({
                "resumen": {
                    "total_ventas": 0,
                    "numero_ventas": 0,
                    "promedio_venta": 0,
                    "mayor_venta": 0
                },
                "metricas_generales": {
                    "tasa_crecimiento": 0,
                    "retorno_cliente": 0,
                    "tasa_abandono": 0
                },
                "metricas_inventario": {
                    "rotacion": 0,
                    "productos_agotados": 0,
                    "dias_inventario": 0
                },
                "ventas_por_categoria": [],
                "metricas_financieras": {
                    "margen_bruto": 0,
                    "margen_operativo": 0,
                    "costo_venta_promedio": 0
                },
                "ventas_por_dia": [],
                "top_clientes": [],
                "patrones_venta": {
                    "diarios": [],
                    "semanales": [],
                    "mensuales": []
                },
                "prediccion_ventas": {
                    "prediccion": 0,
                    "confianza": 0
                },
                "rendimiento_vendedores": [],
                "detalle_ventas": []
            })

        # Calcular resumen
        total_ventas = sum(float(f.total or 0) for f in facturas)
        numero_ventas = len(facturas)
        promedio_venta = total_ventas / numero_ventas if numero_ventas > 0 else 0
        mayor_venta = max((float(f.total or 0) for f in facturas), default=0)

        # Top clientes
        clientes_ventas = {}
        for factura in facturas:
            if factura.cliente:
                nombre = factura.cliente.nombre
                clientes_ventas[nombre] = clientes_ventas.get(nombre, 0) + float(factura.total or 0)

        top_clientes = [
            {"cliente": k, "total": float(v)} 
            for k, v in sorted(clientes_ventas.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Ventas por día
        ventas_por_dia = [{
            "fecha": factura.fecha.strftime('%Y-%m-%d'),
            "total": float(factura.total or 0)
        } for factura in facturas]

        # Obtener datos de patrones
        patrones_diarios = get_patrones_diarios() or []
        patrones_semanales = get_patrones_semanales() or []
        patrones_mensuales = get_patrones_mensuales() or []

        # Predicción de ventas
        prediccion = predict_next_month() or {"prediccion": 0, "confianza": 0}

        # Rendimiento de vendedores
        rendimiento = []
        if vendedor_id:
            ventas_hora = get_ventas_por_hora(vendedor_id) or {}
            rendimiento = [{"vendedor": k, "total": float(v)} for k, v in ventas_hora.items()]

        return jsonify({
            "resumen": {
                "total_ventas": float(total_ventas),
                "numero_ventas": numero_ventas,
                "promedio_venta": float(promedio_venta),
                "mayor_venta": float(mayor_venta)
            },
            "patrones_venta": {
                "diarios": patrones_diarios,
                "semanales": patrones_semanales,
                "mensuales": patrones_mensuales
            },
            "metricas_generales": {
                "tasa_crecimiento": calculate_growth_rate() or 0,
                "retorno_cliente": calculate_customer_return_rate() or 0,
                "tasa_abandono": calculate_churn_rate() or 0
            },
            "metricas_inventario": get_metricas_inventario() or {
                "rotacion": 0,
                "productos_agotados": 0,
                "dias_inventario": 0
            },
            "ventas_por_categoria": get_ventas_por_categoria(facturas) or [],
            "metricas_financieras": {
                "margen_bruto": calculate_gross_margin() or 0,
                "margen_operativo": calculate_operating_margin() or 0,
                "costo_venta_promedio": calculate_average_cogs() or 0
            },
            "ventas_por_dia": ventas_por_dia,
            "top_clientes": top_clientes,
            "patrones_venta": {
                "diarios": patrones_diarios,
                "semanales": patrones_semanales,
                "mensuales": patrones_mensuales
            },
            "prediccion_ventas": prediccion,
            "rendimiento_vendedores": rendimiento,
            "detalle_ventas": [{
                'fecha': factura.fecha.strftime('%Y-%m-%d'),
                'numero_factura': factura.numero,
                'cliente': factura.cliente.nombre if factura.cliente else 'N/A',
                'vendedor': factura.vendedor.nombre if factura.vendedor else 'N/A',
                'tipo_venta': factura.tipo,
                'total': float(factura.total or 0)
            } for factura in facturas]
        })
        
    except Exception as e:
        print(f"Error detallado en reporte_ventas: {str(e)}")
        current_app.logger.error(f"Error generando reporte: {str(e)}")
        return jsonify({"error": "Error al generar el reporte", "details": str(e)}), 500  
    
@facturacion_bp.route('/api/reporte-ventas/cliente/<int:cliente_id>', methods=['GET'])
@login_required
def get_detalle_cliente(cliente_id):
    try:
        # Obtener todas las facturas del cliente
        facturas = Facturacion.query.filter_by(cliente_id=cliente_id).all()
        
        return jsonify({
            "historial_compras": [{
                "fecha": factura.fecha,
                "total": factura.total,
                "productos_frecuentes": get_productos_frecuentes(factura),
                "metodos_pago": get_metodos_pago(factura),
                "descuentos_aplicados": factura.descuento_monto,
                "vendedor": factura.vendedor.nombre
            } for factura in facturas],
            "estadisticas": {
                "promedio_compra": calculate_promedio(facturas),
                "frecuencia_compra": get_frecuencia_compra(facturas),
                "productos_preferidos": get_productos_preferidos(facturas),
                "total_historico": sum(f.total for f in facturas)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/reporte-ventas/categoria/<string:categoria>', methods=['GET'])
@login_required
def get_detalle_categoria(categoria):
    try:
        # Análisis detallado de la categoría
        return jsonify({
            "productos_mas_vendidos": get_top_productos(categoria),
            "tendencia_mensual": get_tendencia_mensual(categoria),
            "margen_ganancia": calculate_margen(categoria),
            "clientes_principales": get_top_clientes_categoria(categoria),
            "comparativa_otras_categorias": get_comparativa_categorias(),
            "stock_actual": get_stock_categoria(categoria)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/reporte-ventas/vendedor/<int:vendedor_id>', methods=['GET'])
@login_required
def get_detalle_vendedor(vendedor_id):
    try:
        return jsonify({
            "metricas_rendimiento": {
                "ventas_por_hora": get_ventas_por_hora(vendedor_id),
                "tasa_conversion": calculate_tasa_conversion(vendedor_id),
                "tickets_promedio": get_ticket_promedio(vendedor_id),
                "productos_mas_vendidos": get_productos_vendedor(vendedor_id),
                "clientes_frecuentes": get_clientes_vendedor(vendedor_id)
            },
            "historico_ventas": get_historico_vendedor(vendedor_id),
            "comisiones": calculate_comisiones(vendedor_id)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/reporte-ventas/metodo-pago/<string:metodo>', methods=['GET'])
@login_required
def get_detalle_metodo_pago(metodo):
    try:
        return jsonify({
            "volumen_transacciones": get_volumen_transacciones(metodo),
            "ticket_promedio": get_ticket_promedio_metodo(metodo),
            "horarios_preferidos": get_horarios_preferidos(metodo),
            "tasa_rechazo": get_tasa_rechazo(metodo),
            "comparativa_otros_metodos": get_comparativa_metodos()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/reporte-ventas/kpis', methods=['GET'])
@login_required
def get_kpis():
    try:
        return jsonify({
            "metricas_generales": {
                "tasa_crecimiento": calculate_growth_rate(),
                "retorno_cliente": calculate_customer_return_rate(),
                "lifetime_value": calculate_customer_lifetime_value(),
                "tasa_abandono": calculate_churn_rate()
            },
            "metricas_inventario": {
                "rotacion": calculate_inventory_turnover(),
                "productos_agotados": get_stockouts(),
                "dias_inventario": calculate_days_inventory()
            },
            "metricas_financieras": {
                "margen_bruto": calculate_gross_margin(),
                "margen_operativo": calculate_operating_margin(),
                "costo_venta_promedio": calculate_average_cogs()
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@facturacion_bp.route('/api/reporte-ventas/analisis-temporal', methods=['GET'])
@login_required
def get_analisis_temporal():
    try:
        return jsonify({
            "comparativa_periodos": {
                "diaria": get_comparativa_diaria(),
                "semanal": get_comparativa_semanal(),
                "mensual": get_comparativa_mensual(),
                "anual": get_comparativa_anual()
            },
            "estacionalidad": {
                "patrones_diarios": get_patrones_diarios(),
                "patrones_semanales": get_patrones_semanales(),
                "patrones_mensuales": get_patrones_mensuales()
            },
            "predicciones": {
                "proximo_mes": predict_next_month(),
                "tendencias": get_tendencias()
            }
        })
    except Exception as e:
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
        print("Datos recibidos:", data)
        
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Datos inválidos"}), 400
        
        # Validar campos obligatorios
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
            
            # Validaciones básicas
            if data['tipo'] not in ['contado', 'credito']:
                return jsonify({"error": "Tipo de factura inválido"}), 400
            
            if data['tipo'] == 'credito' and not cliente_id:
                return jsonify({"error": "El cliente es obligatorio para facturas a crédito"}), 400
            
            if data['tipo_pago'] not in ['efectivo', 'tarjeta', 'transferencia', 'cheque']:
                return jsonify({"error": "Tipo de pago inválido"}), 400
            
            if data['moneda'] not in ['DOP', 'USD']:
                return jsonify({"error": "Moneda inválida"}), 400
            
            # Obtener vendedor
            vendedor = None
            if data.get('vendedor_id'):
                vendedor = Vendedor.query.filter_by(id=int(data['vendedor_id']), activo=True).first()
            if not vendedor:
                vendedor = obtener_vendedor_principal()
                if not vendedor:
                    return jsonify({"error": "Error al obtener el vendedor"}), 500

            # Validar tienda
            tienda = TiendaFactura.query.get(tienda_id)
            if not tienda:
                return jsonify({"error": "Tienda no encontrada"}), 404
            if not tienda.activa:
                return jsonify({"error": "La tienda seleccionada no está activa"}), 400
            if tienda.moneda != data['moneda']:
                return jsonify({"error": f"La moneda debe ser {tienda.moneda}"}), 400

            # Generar número de factura
            ultimo_numero = Facturacion.query.order_by(Facturacion.numero.desc()).first()
            siguiente_numero = str(int(ultimo_numero.numero.replace('F', '')) + 1) if ultimo_numero else '1'
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
            items_data = data.get('items', [])
            
            if not items_data:
                return jsonify({"error": "La factura debe contener al menos un item"}), 400

            for item_data in items_data:
                try:
                    item_id = int(item_data.get('item_id'))
                    cantidad = int(item_data.get('cantidad'))
                    precio = float(item_data.get('precio_unitario'))
                    itbis = float(item_data.get('itbis', 0) or 0)
                    override_code = item_data.get('override_code')

                    # Obtener producto
                    producto = db.session.query(InventarioItem).with_for_update().filter_by(id=item_id).first()
                    if not producto:
                        return jsonify({"error": f"Producto no encontrado: {item_id}"}), 404

                    # Crear ítem de factura
                    item_factura = ItemFactura(
                        item_id=producto.id,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        itbis=itbis,
                        comentario=item_data.get('comentario', ''),
                        override_code=override_code
                    )

                    try:
                        # Procesar inventario usando la lógica del modelo
                        item_factura.procesar_inventario()
                    except ValueError as e:
                        if isinstance(e.args[0], dict) and e.args[0].get('error') == 'stock_insuficiente':
                            return jsonify(e.args[0]), 400
                        raise

                    # Calcular totales
                    subtotal = cantidad * precio
                    itbis_monto = subtotal * (itbis / 100)
                    total += subtotal + itbis_monto

                    nueva_factura.items.append(item_factura)
                    print(f"Item agregado a la factura: {producto.nombre}")

                except Exception as e:
                    print(f"Error procesando item: {str(e)}")
                    db.session.rollback()
                    return jsonify({"error": str(e)}), 500

            nueva_factura.total = round(float(total), 2)

            db.session.add(nueva_factura)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Factura creada exitosamente",
                "factura_id": nueva_factura.id,
                "numero": nueva_factura.numero,
                "total": nueva_factura.total
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error en procesamiento: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
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
            try:
                item_id = int(item_data.get('item_id'))
                cantidad = int(item_data.get('cantidad'))
                precio = float(item_data.get('precio_unitario'))
                override_code = item_data.get('override_code')
                
                producto = InventarioItem.query.get(item_id)
                
                # Dejar que el modelo maneje la validación de stock
                item_factura = ItemFactura(
                    item_id=item_id,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    itbis=float(item_data.get('itbis', 0)),
                    comentario=item_data.get('comentario', ''),
                    override_code=override_code
                )
                factura.items.append(item_factura)  # Cambiado de nueva_factura a factura

            except ValueError as e:
                if isinstance(e.args[0], dict) and e.args[0].get('error') == 'stock_insuficiente':
                    return jsonify(e.args[0]), 400
                raise

        db.session.commit()  # Cambiado para solo hacer commit
        return jsonify({"success": True}), 200  # Cambiado a 200 para edición exitosa

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
        
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