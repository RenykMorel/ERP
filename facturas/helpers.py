# Importaciones necesarias
from datetime import datetime, timedelta
from sqlalchemy import func
from .facturas_models import (  # Solo importar los modelos de facturas
    Facturacion, 
    Cliente, 
    TiendaFactura,
    Vendedor,
    NotaCredito,
    NotaDebito,
    ItemPendiente
)
from common.models import (  # Importar los modelos comunes
    ItemFactura,
    ItemPreFactura,
    MovimientoInventario
)
from inventario.inventario_models import InventarioItem  # Importar desde inventario
from extensions import db
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd

# Análisis de Productos y Categorías
def get_productos_frecuentes(factura):
    """Obtiene los productos más frecuentes de una factura"""
    productos = {}
    for item in factura.items:
        if item.item:
            productos[item.item.nombre] = productos.get(item.item.nombre, 0) + item.cantidad
    return sorted(productos.items(), key=lambda x: x[1], reverse=True)

def get_metodos_pago(factura):
    """Obtiene los métodos de pago utilizados"""
    return {
        'metodo': factura.tipo_pago,
        'monto': float(factura.total)
    }

def calculate_promedio(facturas):
    """Calcula el promedio de compras"""
    if not facturas:
        return 0
    return sum(f.total for f in facturas) / len(facturas)

def get_frecuencia_compra(facturas):
    """Analiza la frecuencia de compra"""
    if not facturas:
        return []
        
    fechas = sorted([f.fecha for f in facturas])
    diferencias = [(fechas[i+1] - fechas[i]).days for i in range(len(fechas)-1)]
    
    return {
        'promedio_dias_entre_compras': sum(diferencias) / len(diferencias) if diferencias else 0,
        'primera_compra': fechas[0].strftime('%Y-%m-%d'),
        'ultima_compra': fechas[-1].strftime('%Y-%m-%d')
    }

def get_volumen_transacciones(metodo):
    """Obtiene el volumen de transacciones por método de pago"""
    facturas = db.session.query(Facturacion).filter_by(
        tipo_pago=metodo,
        estatus='pagada'
    ).all()
    
    return {
        'total_transacciones': len(facturas),
        'monto_total': sum(f.total for f in facturas),
        'promedio_transaccion': sum(f.total for f in facturas) / len(facturas) if facturas else 0
    }

def get_ticket_promedio_metodo(metodo):
    """Calcula el ticket promedio por método de pago"""
    facturas = db.session.query(Facturacion).filter_by(
        tipo_pago=metodo,
        estatus='pagada'
    ).all()
    
    return sum(f.total for f in facturas) / len(facturas) if facturas else 0

def get_horarios_preferidos(metodo):
    """Analiza los horarios preferidos para cada método de pago"""
    facturas = db.session.query(Facturacion).filter_by(
        tipo_pago=metodo,
        estatus='pagada'
    ).all()
    
    horarios = {}
    for factura in facturas:
        hora = factura.fecha_creacion.hour
        horarios[hora] = horarios.get(hora, 0) + 1
    
    return [{'hora': h, 'frecuencia': f} for h, f in sorted(horarios.items())]

# ... resto de las funciones ...

def get_tasa_rechazo(metodo):
    """Calcula la tasa de rechazo por método de pago"""
    total_facturas = db.session.query(Facturacion).filter_by(tipo_pago=metodo).count()
    facturas_anuladas = db.session.query(Facturacion).filter_by(
        tipo_pago=metodo,
        estatus='anulada'
    ).count()
    
    return (facturas_anuladas / total_facturas * 100) if total_facturas > 0 else 0

def get_comparativa_metodos():
    """Compara el uso de diferentes métodos de pago"""
    metodos = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        metodos[factura.tipo_pago] = metodos.get(factura.tipo_pago, 0) + factura.total
        
    return [{'metodo': k, 'total': v} for k, v in sorted(metodos.items(), key=lambda x: x[1], reverse=True)]

# Análisis Temporal y Predicciones
def get_comparativa_diaria():
    """Obtiene comparativa de ventas diarias"""
    return get_ventas_periodo('dia')

def get_comparativa_semanal():
    """Obtiene comparativa de ventas semanales"""
    return get_ventas_periodo('semana')

def get_comparativa_mensual():
    """Obtiene comparativa de ventas mensuales"""
    return get_ventas_periodo('mes')

def get_comparativa_anual():
    """Obtiene comparativa de ventas anuales"""
    return get_ventas_periodo('año')

def get_ventas_periodo(periodo):
    """Función auxiliar para obtener ventas por periodo"""
    ventas = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    formato = {
        'dia': '%Y-%m-%d',
        'semana': '%Y-%W',
        'mes': '%Y-%m',
        'año': '%Y'
    }
    
    for factura in facturas:
        periodo_key = factura.fecha.strftime(formato[periodo])
        ventas[periodo_key] = ventas.get(periodo_key, 0) + factura.total
        
    return [{'periodo': k, 'total': v} for k, v in sorted(ventas.items())]

def predict_next_month():
    """Predice las ventas del próximo mes usando regresión lineal"""
    try:
        # Get sales data from last 6 months
        six_months_ago = datetime.now() - timedelta(days=180)
        ventas = db.session.query(
            func.date_trunc('month', Facturacion.fecha).label('mes'),
            func.sum(Facturacion.total).label('total')
        ).filter(
            Facturacion.estatus == 'pagada',
            Facturacion.fecha >= six_months_ago
        ).group_by(
            func.date_trunc('month', Facturacion.fecha)
        ).order_by('mes').all()

        if len(ventas) < 2:
            return {'prediccion': 0, 'confianza': 0}

        # Prepare data for regression
        X = np.array(range(len(ventas))).reshape(-1, 1)
        y = np.array([float(venta.total or 0) for venta in ventas])

        model = LinearRegression()
        model.fit(X, y)
        
        next_month_pred = model.predict([[len(ventas)]])[0]
        score = model.score(X, y)

        return {
            'prediccion': float(max(0, next_month_pred)),
            'confianza': float(score * 100)
        }
    except Exception as e:
        print(f"Error en predicción: {str(e)}")
        return {'prediccion': 0, 'confianza': 0}

def get_tendencias():
    """Analiza tendencias generales de ventas"""
    ventas_mensuales = get_comparativa_mensual()
    if not ventas_mensuales:
        return None
        
    totales = [v['total'] for v in ventas_mensuales]
    tendencia = 'creciente' if totales[-1] > totales[0] else 'decreciente'
    variacion = ((totales[-1] - totales[0]) / totales[0] * 100) if totales[0] > 0 else 0
    
    return {
        'tendencia': tendencia,
        'variacion_porcentual': variacion,
        'maximo': max(totales),
        'minimo': min(totales),
        'promedio': sum(totales) / len(totales)
    }

# KPIs y Métricas de Negocio
def calculate_growth_rate():
    """Calcula la tasa de crecimiento"""
    ventas_mensuales = get_comparativa_mensual()
    if len(ventas_mensuales) < 2:
        return 0
        
    mes_anterior = ventas_mensuales[-2]['total']
    mes_actual = ventas_mensuales[-1]['total']
    
    return ((mes_actual - mes_anterior) / mes_anterior * 100) if mes_anterior > 0 else 0

def calculate_customer_return_rate():
    """Calcula la tasa de retorno de clientes"""
    clientes_totales = db.session.query(Cliente).count()
    clientes_recurrentes = db.session.query(
        Cliente.id,
        func.count(Facturacion.id).label('compras')
    ).join(Facturacion).group_by(Cliente.id).having(func.count(Facturacion.id) > 1).count()
    
    return (clientes_recurrentes / clientes_totales * 100) if clientes_totales > 0 else 0

def calculate_churn_rate():
    """Calcula la tasa de abandono de clientes"""
    periodo = datetime.now() - timedelta(days=90)
    clientes_totales = db.session.query(Cliente).count()
    clientes_activos = db.session.query(Cliente).join(Facturacion).filter(
        Facturacion.fecha >= periodo
    ).distinct().count()
    
    return ((clientes_totales - clientes_activos) / clientes_totales * 100) if clientes_totales > 0 else 0

def calculate_inventory_turnover():
    """Calcula la rotación del inventario"""
    items = db.session.query(InventarioItem).all()
    total_costo_inventario = sum(item.stock * item.costo for item in items)
    
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    costo_ventas = sum(
        item.cantidad * item.item.costo
        for factura in facturas
        for item in factura.items
        if item.item
    )
    
    return costo_ventas / total_costo_inventario if total_costo_inventario > 0 else 0

def calculate_days_inventory():
    """Calcula los días de inventario"""
    rotacion = calculate_inventory_turnover()
    return 365 / rotacion if rotacion > 0 else 0

def calculate_gross_margin():
    """Calcula el margen bruto"""
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    ingresos = sum(factura.total for factura in facturas)
    costo_ventas = sum(
        item.cantidad * item.item.costo
        for factura in facturas
        for item in factura.items
        if item.item
    )
    
    return ((ingresos - costo_ventas) / ingresos * 100) if ingresos > 0 else 0

def calculate_operating_margin():
    """Calcula el margen operativo"""
    margen_bruto = calculate_gross_margin()
    # Aquí podrías restar gastos operativos si tienes esa información
    gastos_operativos = 20  # Ejemplo: 20% de gastos operativos
    return margen_bruto - gastos_operativos

# Agregar estas funciones a helpers.py

def get_productos_preferidos(facturas):
    """Obtiene los productos preferidos de un conjunto de facturas"""
    productos = {}
    for factura in facturas:
        for item in factura.items:
            if item.item:
                key = item.item.nombre
                productos[key] = productos.get(key, 0) + item.cantidad
    
    return sorted(
        [{'producto': k, 'cantidad': v} for k, v in productos.items()],
        key=lambda x: x['cantidad'],
        reverse=True
    )[:5]  # Top 5 productos

def get_top_clientes_categoria(categoria):
    """Obtiene los principales clientes por categoría"""
    clientes = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        if factura.cliente:
            for item in factura.items:
                if item.item and item.item.categoria == categoria:
                    key = factura.cliente.nombre
                    clientes[key] = clientes.get(key, 0) + (item.cantidad * item.precio_unitario)
    
    return sorted(
        [{'cliente': k, 'total': v} for k, v in clientes.items()],
        key=lambda x: x['total'],
        reverse=True
    )[:5]

def get_comparativa_categorias():
    """Compara diferentes categorías de productos"""
    categorias = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        for item in factura.items:
            if item.item and item.item.categoria:
                categoria = item.item.categoria
                categorias[categoria] = categorias.get(categoria, 0) + (item.cantidad * item.precio_unitario)
    
    return sorted(
        [{'categoria': k, 'total': v} for k, v in categorias.items()],
        key=lambda x: x['total'],
        reverse=True
    )

def get_stock_categoria(categoria):
    """Obtiene información del stock por categoría"""
    items = db.session.query(InventarioItem).filter_by(categoria=categoria).all()
    
    total_stock = sum(item.stock for item in items)
    valor_total = sum(item.stock * item.costo for item in items)
    items_bajo_stock = len([item for item in items if item.stock <= item.stock_minimo])
    
    return {
        'total_items': len(items),
        'total_stock': total_stock,
        'valor_total': valor_total,
        'items_bajo_stock': items_bajo_stock,
        'promedio_stock': total_stock / len(items) if items else 0
    }

def get_stockouts():
    """Obtiene productos agotados"""
    return db.session.query(InventarioItem).filter(
        InventarioItem.stock <= 0
    ).count()

def get_patrones_diarios():
    """Analiza patrones de venta diarios"""
    try:
        ventas = db.session.query(
            func.date_format(Facturacion.fecha, '%W').label('dia'),
            func.sum(Facturacion.total).label('total')
        ).filter(
            Facturacion.estatus == 'pagada'
        ).group_by('dia').all()

        # Asegurar datos para todos los días
        dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        resultados = []

        for dia in dias:
            venta = next((v for v in ventas if v.dia.lower() == dia.lower()), None)
            resultados.append({
                'dia': dia,
                'total': float(venta.total) if venta else 0.0
            })
        
        return resultados
    except Exception as e:
        print(f"Error en patrones diarios: {str(e)}")
        return []

def get_patrones_semanales():
    """Analiza patrones de venta semanales"""
    ventas_por_semana = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        semana = factura.fecha.strftime('%V')  # Número de semana
        ventas_por_semana[semana] = ventas_por_semana.get(semana, 0) + factura.total
        
    return [{'semana': k, 'total': v} for k, v in sorted(ventas_por_semana.items())]

def get_metricas_inventario():
    """Calcula todas las métricas de inventario"""
    try:
        # Obtener todos los productos
        productos = InventarioItem.query.filter_by(tipo='producto').all()
        
        if not productos:
            return {
                "rotacion": 0,
                "productos_agotados": 0,
                "dias_inventario": 0,
                "valor_total_inventario": 0
            }

        # Calcular productos agotados
        productos_agotados = sum(1 for p in productos if p.stock <= 0)

        # Calcular valor total del inventario
        valor_total = sum(p.stock * p.costo for p in productos)

        # Calcular ventas del último mes
        un_mes_atras = datetime.now() - timedelta(days=30)
        ventas_mes = db.session.query(
            ItemFactura
        ).join(
            Facturacion
        ).filter(
            Facturacion.fecha >= un_mes_atras,
            Facturacion.estatus == 'pagada'
        ).all()

        # Calcular costo de ventas
        costo_ventas = sum(
            item.cantidad * item.item.costo 
            for item in ventas_mes 
            if item.item
        )

        # Calcular rotación
        rotacion = costo_ventas / valor_total if valor_total > 0 else 0

        # Calcular días de inventario
        dias_inventario = 30 / rotacion if rotacion > 0 else 0

        return {
            "rotacion": round(rotacion, 2),
            "productos_agotados": productos_agotados,
            "dias_inventario": round(dias_inventario, 0),
            "valor_total_inventario": round(valor_total, 2)
        }
    except Exception as e:
        print(f"Error calculando métricas de inventario: {str(e)}")
        return {
            "rotacion": 0,
            "productos_agotados": 0,
            "dias_inventario": 0,
            "valor_total_inventario": 0
        }

def get_ventas_por_categoria(facturas):
    """Calcula las ventas por categoría"""
    ventas_categoria = {}
    
    # Iterar sobre las facturas y sus items
    for factura in facturas:
        for item in factura.items:
            if item.item and item.item.categoria:  # Verificar que el item y su categoría existen
                categoria = item.item.categoria
                subtotal = item.cantidad * item.precio_unitario
                ventas_categoria[categoria] = ventas_categoria.get(categoria, 0) + subtotal

    # Ordenar por monto de ventas
    return [
        {"categoria": categoria, "total": float(total)}
        for categoria, total in sorted(
            ventas_categoria.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
    ]
    
def get_metricas_inventario():
    """Calcula todas las métricas de inventario"""
    try:
        # Obtener todos los productos
        productos = InventarioItem.query.filter_by(tipo='producto').all()
        
        if not productos:
            return {
                "rotacion": 0,
                "productos_agotados": 0,
                "dias_inventario": 0,
                "valor_total_inventario": 0
            }

        # Calcular productos agotados
        productos_agotados = sum(1 for p in productos if p.stock <= 0)

        # Calcular valor total del inventario
        valor_total = sum(p.stock * p.costo for p in productos)

        # Calcular ventas del último mes
        un_mes_atras = datetime.now() - timedelta(days=30)
        ventas_mes = db.session.query(
            ItemFactura
        ).join(
            Facturacion
        ).filter(
            Facturacion.fecha >= un_mes_atras,
            Facturacion.estatus == 'pagada'
        ).all()

        # Calcular costo de ventas
        costo_ventas = sum(
            item.cantidad * item.item.costo 
            for item in ventas_mes 
            if item.item
        )

        # Calcular rotación
        rotacion = costo_ventas / valor_total if valor_total > 0 else 0

        # Calcular días de inventario
        dias_inventario = 30 / rotacion if rotacion > 0 else 0

        return {
            "rotacion": round(rotacion, 2),
            "productos_agotados": productos_agotados,
            "dias_inventario": round(dias_inventario, 0),
            "valor_total_inventario": round(valor_total, 2)
        }
    except Exception as e:
        print(f"Error calculando métricas de inventario: {str(e)}")
        return {
            "rotacion": 0,
            "productos_agotados": 0,
            "dias_inventario": 0,
            "valor_total_inventario": 0
        }
        
        
# Agregar al archivo facturas_models.py o en un nuevo archivo helpers.py

def generate_default_template(factura):
    """Genera el HTML por defecto para una factura"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                padding: 20px;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
            }}
            .company-info {{
                flex: 1;
            }}
            .invoice-details {{
                text-align: right;
            }}
            .client-info {{
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f5f5f5;
            }}
            .totals {{
                text-align: right;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company-info">
                <h1>Tu Empresa</h1>
                <p>Dirección: Calle Principal #123</p>
                <p>Tel: (123) 456-7890</p>
                <p>RNC: 123456789</p>
            </div>
            <div class="invoice-details">
                <h2>FACTURA DE CONSUMO</h2>
                <p>No.: {factura.numero}</p>
                <p>Fecha: {factura.fecha.strftime('%d/%m/%Y')}</p>
                <p>Vendedor: {factura.vendedor.nombre if factura.vendedor else 'N/A'}</p>
                <p>Tipo: {factura.tipo_pago}</p>
            </div>
        </div>

        <div class="client-info">
            <h3>Cliente</h3>
            <p>Nombre: {factura.cliente.nombre if factura.cliente else 'N/A'}</p>
            <p>RNC/Cédula: {factura.cliente.ruc if factura.cliente else 'N/A'}</p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Descripción</th>
                    <th>Cantidad</th>
                    <th>Precio</th>
                    <th>ITBIS</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {generate_items_html(factura.items)}
            </tbody>
        </table>

        <div class="totals">
            <p>Subtotal: RD${format_currency(factura.total - sum(item.itbis for item in factura.items))}</p>
            <p>ITBIS: RD${format_currency(sum(item.itbis for item in factura.items))}</p>
            <p>Descuento: RD${format_currency(factura.descuento_monto)}</p>
            <p><strong>Total: RD${format_currency(factura.total)}</strong></p>
        </div>

        <div style="margin-top: 40px; font-size: 12px; color: #666;">
            <p>Gracias por su preferencia</p>
            <p>Esta factura es un documento fiscal válido.</p>
        </div>
    </body>
    </html>
    """
    return html_content

def generate_items_html(items):
    """Genera el HTML para los items de la factura"""
    items_html = ""
    for item in items:
        items_html += f"""
            <tr>
                <td>{item.item.nombre if item.item else 'N/A'}</td>
                <td>{item.cantidad}</td>
                <td>RD${format_currency(item.precio_unitario)}</td>
                <td>RD${format_currency(item.itbis)}</td>
                <td>RD${format_currency(item.cantidad * item.precio_unitario)}</td>
            </tr>
        """
    return items_html

def format_currency(amount):
    """Formatea cantidades monetarias"""
    return "{:,.2f}".format(float(amount or 0))        

def get_ventas_por_categoria(facturas):
    """Calcula las ventas por categoría"""
    ventas_categoria = {}
    
    # Iterar sobre las facturas y sus items
    for factura in facturas:
        for item in factura.items:
            if item.item and item.item.categoria:  # Verificar que el item y su categoría existen
                categoria = item.item.categoria
                subtotal = item.cantidad * item.precio_unitario
                ventas_categoria[categoria] = ventas_categoria.get(categoria, 0) + subtotal

    # Ordenar por monto de ventas
    return [
        {"categoria": categoria, "total": float(total)}
        for categoria, total in sorted(
            ventas_categoria.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
    ]    

def get_patrones_mensuales():
    """Analiza patrones de venta mensuales"""
    try:
        ventas_por_mes = {}
        facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
        
        if not facturas:
            return []
            
        for factura in facturas:
            try:
                mes = factura.fecha.strftime('%Y-%m')
                ventas_por_mes[mes] = ventas_por_mes.get(mes, 0) + float(factura.total or 0)
            except Exception as e:
                print(f"Error procesando factura {factura.id}: {str(e)}")
                continue
                
        return [{'mes': k, 'total': float(v)} for k, v in sorted(ventas_por_mes.items())]
        
    except Exception as e:
        print(f"Error en patrones mensuales: {str(e)}")
        return []

# 1. Funciones para el análisis por vendedor
def get_ventas_por_hora(vendedor_id):
    """Obtiene las ventas por hora"""
    try:
        query = db.session.query(
            func.extract('hour', Facturacion.fecha_creacion).label('hora'),
            func.sum(Facturacion.total).label('total')
        ).filter(Facturacion.estatus == 'pagada')

        if vendedor_id:
            query = query.filter(Facturacion.vendedor_id == vendedor_id)

        ventas = query.group_by('hora').all()

        # Asegurar datos para todas las horas
        resultados = []
        for hora in range(24):
            venta = next((v for v in ventas if int(v.hora) == hora), None)
            resultados.append({
                'vendedor': f'{hora:02d}',
                'total': float(venta.total) if venta else 0.0
            })

        return resultados
    except Exception as e:
        print(f"Error en ventas por hora: {str(e)}")
        return []

def get_productos_vendedor(vendedor_id):
    """Obtiene los productos más vendidos por un vendedor"""
    facturas = Facturacion.query.filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    
    productos = {}
    for factura in facturas:
        for item in factura.items:
            if item.item:
                key = item.item.nombre
                productos[key] = productos.get(key, 0) + item.cantidad
                
    return sorted(
        [{'producto': k, 'cantidad': v} for k, v in productos.items()],
        key=lambda x: x['cantidad'],
        reverse=True
    )[:10]

def get_clientes_vendedor(vendedor_id):
    """Obtiene los clientes más frecuentes de un vendedor"""
    facturas = Facturacion.query.filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    
    clientes = {}
    for factura in facturas:
        if factura.cliente:
            key = factura.cliente.nombre
            clientes[key] = clientes.get(key, 0) + 1
            
    return sorted(
        [{'cliente': k, 'frecuencia': v} for k, v in clientes.items()],
        key=lambda x: x['frecuencia'],
        reverse=True
    )[:5]

def calculate_tasa_conversion(vendedor_id):
    """Calcula la tasa de conversión del vendedor"""
    total = Facturacion.query.filter_by(vendedor_id=vendedor_id).count()
    exitosas = Facturacion.query.filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).count()
    
    return (exitosas / total * 100) if total > 0 else 0

def get_historico_vendedor(vendedor_id):
    """Obtiene el histórico de ventas de un vendedor"""
    facturas = Facturacion.query.filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).order_by(Facturacion.fecha).all()
    
    ventas_mes = {}
    for factura in facturas:
        mes = factura.fecha.strftime('%Y-%m')
        ventas_mes[mes] = ventas_mes.get(mes, 0) + factura.total
        
    return [{'mes': k, 'total': v} for k, v in sorted(ventas_mes.items())]

def calculate_comisiones(vendedor_id):
    """Calcula las comisiones del vendedor"""
    facturas = Facturacion.query.filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    
    total_ventas = sum(f.total for f in facturas)
    comision = total_ventas * 0.05  # 5% de comisión
    
    return {
        'total_ventas': total_ventas,
        'porcentaje_comision': 5,
        'monto_comision': comision
    }

# 2. Funciones para el análisis temporal
def get_patrones_diarios():
    """Analiza patrones de venta por día de la semana"""
    try:
        ventas = db.session.query(
            func.extract('dow', Facturacion.fecha).label('dia'),
            func.sum(Facturacion.total).label('total')
        ).filter(
            Facturacion.estatus == 'pagada'
        ).group_by(
            func.extract('dow', Facturacion.fecha)
        ).order_by('dia').all()

        dias = {
            0: 'Domingo', 1: 'Lunes', 2: 'Martes', 
            3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
        }

        resultados = []
        for dia_num in range(7):
            venta = next((v for v in ventas if int(v.dia) == dia_num), None)
            resultados.append({
                'dia': dias[dia_num],
                'total': float(venta.total) if venta else 0
            })
        return resultados
        
    except Exception as e:
        print(f"Error en patrones diarios: {str(e)}")
        return []

def get_patrones_semanales():
    """Obtiene patrones de ventas semanales"""
    facturas = Facturacion.query.filter_by(estatus='pagada').all()
    ventas_semana = {}
    
    for factura in facturas:
        semana = factura.fecha.strftime('%U')
        ventas_semana[semana] = ventas_semana.get(semana, 0) + factura.total
        
    return [{'semana': k, 'total': v} for k, v in sorted(ventas_semana.items())]

def get_patrones_mensuales():
    """Obtiene patrones de ventas mensuales"""
    facturas = Facturacion.query.filter_by(estatus='pagada').all()
    ventas_mes = {}
    
    for factura in facturas:
        mes = factura.fecha.strftime('%B')
        ventas_mes[mes] = ventas_mes.get(mes, 0) + factura.total
        
    return [{'mes': k, 'total': v} for k, v in sorted(ventas_mes.items())]

# 3. Funciones para análisis de productos y categorías
def get_productos_preferidos(facturas):
    """Obtiene los productos preferidos de un conjunto de facturas"""
    productos = {}
    for factura in facturas:
        for item in factura.items:
            if item.item:
                key = item.item.nombre
                productos[key] = productos.get(key, 0) + item.cantidad
    
    return sorted(
        [{'producto': k, 'cantidad': v} for k, v in productos.items()],
        key=lambda x: x['cantidad'],
        reverse=True
    )[:5]

def get_top_clientes_categoria(categoria):
    """Obtiene los principales clientes por categoría"""
    facturas = Facturacion.query.join(ItemFactura).join(
        InventarioItem
    ).filter(
        InventarioItem.categoria == categoria,
        Facturacion.estatus == 'pagada'
    ).all()
    
    clientes = {}
    for factura in facturas:
        if factura.cliente:
            key = factura.cliente.nombre
            total = sum(
                item.cantidad * item.precio_unitario 
                for item in factura.items 
                if item.item and item.item.categoria == categoria
            )
            clientes[key] = clientes.get(key, 0) + total
    
    return sorted(
        [{'cliente': k, 'total': v} for k, v in clientes.items()],
        key=lambda x: x['total'],
        reverse=True
    )[:5]
    
def get_top_productos(categoria):
    """Obtiene los productos más vendidos por categoría"""
    productos = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        for item in factura.items:
            if item.item and item.item.categoria == categoria:
                productos[item.item.nombre] = productos.get(item.item.nombre, 0) + item.cantidad
                
    return sorted(
        [{'producto': k, 'cantidad': v} for k, v in productos.items()],
        key=lambda x: x['cantidad'],
        reverse=True
    )[:10]  # Top 10 productos    

# 4. Funciones para métricas de negocio
def calculate_customer_lifetime_value(cliente_id):
    """Calcula el valor de vida del cliente"""
    facturas = Facturacion.query.filter_by(
        cliente_id=cliente_id,
        estatus='pagada'
    ).all()
    
    if not facturas:
        return {
            'total_historico': 0,
            'promedio_mensual': 0,
            'tiempo_como_cliente': 0
        }
        
    total_compras = sum(f.total for f in facturas)
    primera_compra = min(f.fecha for f in facturas)
    ultima_compra = max(f.fecha for f in facturas)
    tiempo_como_cliente = (ultima_compra - primera_compra).days
    
    return {
        'total_historico': total_compras,
        'promedio_mensual': total_compras * 30 / tiempo_como_cliente if tiempo_como_cliente > 0 else 0,
        'tiempo_como_cliente': tiempo_como_cliente
    }
    
def get_tendencia_mensual(categoria):
    """Obtiene la tendencia mensual de ventas por categoría"""
    ventas_mensuales = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        mes = factura.fecha.strftime('%Y-%m')
        for item in factura.items:
            if item.item and item.item.categoria == categoria:
                ventas_mensuales[mes] = ventas_mensuales.get(mes, 0) + (item.cantidad * item.precio_unitario)
                
    return [{'mes': k, 'total': v} for k, v in sorted(ventas_mensuales.items())]

def get_ticket_promedio(vendedor_id):
    """Calcula el ticket promedio del vendedor"""
    facturas = db.session.query(Facturacion).filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    
    if not facturas:
        return 0
        
    return sum(f.total for f in facturas) / len(facturas)

def get_stockouts():
    """Obtiene la cantidad de productos agotados"""
    try:
        stockouts = db.session.query(InventarioItem).filter(
            InventarioItem.stock <= 0,
            InventarioItem.tipo == 'producto'
        ).count()
        return stockouts
    except Exception as e:
        print(f"Error al obtener stockouts: {str(e)}")
        return 0
    
def get_ventas_por_hora(vendedor_id):
    """Obtiene las ventas por hora"""
    try:
        ventas = db.session.query(
            func.extract('hour', Facturacion.fecha_creacion).label('hora'),
            func.sum(Facturacion.total).label('total')
        ).filter(
            Facturacion.estatus == 'pagada'
        )
        
        if vendedor_id:
            ventas = ventas.filter(Facturacion.vendedor_id == vendedor_id)
            
        ventas = ventas.group_by(
            func.extract('hour', Facturacion.fecha_creacion)
        ).order_by('hora').all()

        resultados = []
        for hora in range(24):
            venta = next((v for v in ventas if int(v.hora) == hora), None)
            resultados.append({
                'vendedor': str(hora).zfill(2),
                'total': float(venta.total) if venta else 0
            })
            
        return resultados
        
    except Exception as e:
        print(f"Error en ventas por hora: {str(e)}")
        return []

def get_productos_preferidos(facturas):
    """Obtiene los productos más comprados en un conjunto de facturas"""
    productos = {}
    for factura in facturas:
        for item in factura.items:
            if item.item:
                key = item.item.nombre
                productos[key] = productos.get(key, 0) + item.cantidad
    return dict(sorted(productos.items(), key=lambda x: x[1], reverse=True)[:5])

def get_top_clientes_categoria(categoria):
    """Obtiene los mejores clientes por categoría"""
    clientes = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        if factura.cliente:
            total_categoria = sum(
                item.cantidad * item.precio_unitario
                for item in factura.items
                if item.item and item.item.categoria == categoria
            )
            if total_categoria > 0:
                clientes[factura.cliente.nombre] = clientes.get(factura.cliente.nombre, 0) + total_categoria
    
    return dict(sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:5])

def get_comparativa_categorias():
    """Compara ventas entre diferentes categorías"""
    categorias = {}
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    for factura in facturas:
        for item in factura.items:
            if item.item and item.item.categoria:
                key = item.item.categoria
                categorias[key] = categorias.get(key, 0) + (item.cantidad * item.precio_unitario)
    
    return categorias

def get_stock_categoria(categoria):
    """Obtiene información del stock por categoría"""
    items = db.session.query(InventarioItem).filter_by(categoria=categoria).all()
    return {
        'total_items': len(items),
        'stock_total': sum(item.stock for item in items),
        'valor_total': sum(item.stock * item.costo for item in items),
        'items_bajo_stock': len([item for item in items if item.stock <= item.stock_minimo])
    }

def calculate_tasa_conversion(vendedor_id):
    """Calcula la tasa de conversión del vendedor"""
    total = db.session.query(Facturacion).filter_by(vendedor_id=vendedor_id).count()
    exitosas = db.session.query(Facturacion).filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).count()
    return (exitosas / total * 100) if total > 0 else 0

def get_ticket_promedio(vendedor_id):
    """Calcula el ticket promedio del vendedor"""
    facturas = db.session.query(Facturacion).filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    return sum(f.total for f in facturas) / len(facturas) if facturas else 0

def get_productos_vendedor(vendedor_id):
    """Obtiene los productos más vendidos por un vendedor"""
    productos = {}
    facturas = db.session.query(Facturacion).filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    
    for factura in facturas:
        for item in factura.items:
            if item.item:
                key = item.item.nombre
                productos[key] = productos.get(key, 0) + item.cantidad
    
    return dict(sorted(productos.items(), key=lambda x: x[1], reverse=True)[:10])

def get_clientes_vendedor(vendedor_id):
    """Obtiene los clientes más frecuentes de un vendedor"""
    clientes = {}
    facturas = db.session.query(Facturacion).filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    
    for factura in facturas:
        if factura.cliente:
            key = factura.cliente.nombre
            clientes[key] = clientes.get(key, 0) + 1
    
    return dict(sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:5])

def get_historico_vendedor(vendedor_id):
    """Obtiene el histórico de ventas de un vendedor"""
    ventas_mes = {}
    facturas = db.session.query(Facturacion).filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).order_by(Facturacion.fecha).all()
    
    for factura in facturas:
        mes = factura.fecha.strftime('%Y-%m')
        ventas_mes[mes] = ventas_mes.get(mes, 0) + factura.total
    
    return ventas_mes

def calculate_comisiones(vendedor_id):
    """Calcula las comisiones del vendedor"""
    facturas = db.session.query(Facturacion).filter_by(
        vendedor_id=vendedor_id,
        estatus='pagada'
    ).all()
    
    total_ventas = sum(f.total for f in facturas)
    comision = total_ventas * 0.05  # 5% de comisión base
    
    return {
        'total_ventas': total_ventas,
        'porcentaje_comision': 5,
        'monto_comision': comision
    }

def get_patrones_diarios():
    """Analiza patrones de venta diarios"""
    try:
        ventas_por_dia = {}
        facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
        
        if not facturas:
            return []
            
        for factura in facturas:
            try:
                dia = factura.fecha.strftime('%A')  # Nombre del día
                ventas_por_dia[dia] = ventas_por_dia.get(dia, 0) + float(factura.total or 0)
            except Exception as e:
                print(f"Error procesando factura {factura.id}: {str(e)}")
                continue
                
        # Asegurar que todos los días estén representados
        dias_semana = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        resultado = []
        
        for dia in dias_semana:
            resultado.append({
                'dia': dia,
                'total': float(ventas_por_dia.get(dia, 0))
            })
            
        return resultado
        
    except Exception as e:
        print(f"Error en patrones diarios: {str(e)}")
        return []

def get_patrones_semanales():
    """Analiza patrones de venta por semana"""
    try:
        ventas = db.session.query(
            func.date_trunc('week', Facturacion.fecha).label('semana'),
            func.sum(Facturacion.total).label('total')
        ).filter(
            Facturacion.estatus == 'pagada'
        ).group_by(
            func.date_trunc('week', Facturacion.fecha)
        ).order_by('semana').all()

        return [{
            'semana': venta.semana.strftime('%Y-%m-%d'),
            'total': float(venta.total or 0)
        } for venta in ventas]
    except Exception as e:
        print(f"Error en patrones semanales: {str(e)}")
        return []

def get_patrones_mensuales():
    """Analiza patrones de venta por mes"""
    try:
        ventas = db.session.query(
            func.date_trunc('month', Facturacion.fecha).label('mes'),
            func.sum(Facturacion.total).label('total')
        ).filter(
            Facturacion.estatus == 'pagada'
        ).group_by(
            func.date_trunc('month', Facturacion.fecha)
        ).order_by('mes').all()

        return [{
            'mes': venta.mes.strftime('%Y-%m'),
            'total': float(venta.total or 0)
        } for venta in ventas]
    except Exception as e:
        print(f"Error en patrones mensuales: {str(e)}")
        return [] 

def calculate_margen(categoria):
    """Calcula el margen de ganancia por categoría"""
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    total_ventas = 0
    total_costo = 0
    
    for factura in facturas:
        for item in factura.items:
            if item.item and item.item.categoria == categoria:
                total_ventas += item.cantidad * item.precio_unitario
                total_costo += item.cantidad * float(item.item.costo)
                
    margen = ((total_ventas - total_costo) / total_ventas * 100) if total_ventas > 0 else 0
    
    return {
        'total_ventas': total_ventas,
        'total_costo': total_costo,
        'margen_porcentaje': margen
    }    

def calculate_average_cogs():
    """Calcula el costo de venta promedio"""
    facturas = db.session.query(Facturacion).filter_by(estatus='pagada').all()
    
    total_items = sum(
        item.cantidad
        for factura in facturas
        for item in factura.items
    )
    
    costo_total = sum(
        item.cantidad * item.item.costo
        for factura in facturas
        for item in factura.items
        if item.item
    )
    
    return costo_total / total_items if total_items > 0 else 0