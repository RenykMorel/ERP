# routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required
from .models import ClienteCxc, CuentaPorCobrar
from extensions import db
from sqlalchemy import func, text, desc
from datetime import datetime, timedelta, date
from sqlalchemy.sql import text as sql_text
import re
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError


cxc_bp = Blueprint('cxc', __name__, url_prefix='/cxc')

@cxc_bp.route('/clientes', methods=['GET'])
@login_required
def clientes():
    try:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            query = ClienteCxc.query
            
            # Aplicar filtros si existen
            if request.args.get('id'):
                query = query.filter(ClienteCxc.id == request.args.get('id'))
            if request.args.get('nombre'):
                query = query.filter(ClienteCxc.nombre.ilike(f"%{request.args.get('nombre')}%"))
            if request.args.get('documento'):
                query = query.filter(ClienteCxc.documento.ilike(f"%{request.args.get('documento')}%"))
            if request.args.get('estado'):
                query = query.filter(ClienteCxc.estado == request.args.get('estado'))
            
            clientes = query.all()
            
            return jsonify({
                'status': 'success',
                'clientes': [cliente.to_dict() for cliente in clientes],
                'total': len(clientes)
            })
        else:
            return render_template('cxc/clientes.html')
    except Exception as e:
        print(f"Error al obtener clientes: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@cxc_bp.route('/crear-cliente', methods=['GET', 'POST'])
@login_required
def crear_cliente():
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            data = request.get_json() if request.is_json else request.form
            
            # Validar campos requeridos
            campos_requeridos = ['tipo_documento', 'documento', 'nombre']
            for campo in campos_requeridos:
                if not data.get(campo):
                    return jsonify({
                        "status": "error",
                        "message": f"El campo {campo} es requerido"
                    }), 400

            # Crear nuevo cliente con todos los campos
            nuevo_cliente = ClienteCxc(
                tipo_documento=data.get('tipo_documento'),
                documento=data.get('documento'),
                nombre=data.get('nombre'),
                direccion=data.get('direccion'),
                provincia=data.get('provincia'),
                municipio=data.get('municipio'),
                telefono=data.get('telefono_principal'),
                telefono_secundario=data.get('telefono_secundario'),
                email=data.get('email'),
                tienda=data.get('tienda'),
                tipo_factura=data.get('tipo_factura'),
                limite_credito=float(data.get('limite_credito', 0)),
                dias_gracia=int(data.get('dias_atraso', 0)),
                retencion_itbis=float(data.get('retencion_itbis', 0)),
                retencion_isr=float(data.get('retencion_isr', 0)),
                estado=data.get('estado', 'activo'),
                tipo_cliente_id=data.get('tipo')
            )

            # Agregar y guardar en la base de datos
            db.session.add(nuevo_cliente)
            db.session.commit()

            # Retornar respuesta exitosa
            return jsonify({
                "status": "success",
                "message": "Cliente creado exitosamente",
                "data": {
                    "id": nuevo_cliente.id,
                    "nombre": nuevo_cliente.nombre,
                    "documento": nuevo_cliente.documento
                }
            }), 201

        except ValueError as ve:
            db.session.rollback()
            print(f"Error de validación: {str(ve)}")
            return jsonify({
                "status": "error",
                "message": "Error en los datos proporcionados",
                "details": str(ve)
            }), 400

        except Exception as e:
            db.session.rollback()
            print(f"Error creando cliente: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Error interno del servidor",
                "details": str(e)
            }), 500

    # Para peticiones GET, renderizar el template
    return render_template('cxc/clientes.html')

# Función auxiliar para validar el formato del documento según el tipo
def validar_documento(tipo, numero):
    if tipo == 'cedula':
        # Validar cédula (11 dígitos)
        if not re.match(r'^\d{11}$', numero):
            raise ValueError('Formato de cédula inválido')
    elif tipo == 'rnc':
        # Validar RNC (9 dígitos)
        if not re.match(r'^\d{9}$', numero):
            raise ValueError('Formato de RNC inválido')
    elif tipo == 'pasaporte':
        # Validar pasaporte (alfanumérico, mínimo 6 caracteres)
        if not re.match(r'^[A-Za-z0-9]{6,}$', numero):
            raise ValueError('Formato de pasaporte inválido')
    return True

# Función auxiliar para validar el email
def validar_email(email):
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError('Formato de email inválido')
    return True

# Función auxiliar para validar el teléfono
def validar_telefono(telefono):
    if telefono and not re.match(r'^\(\d{3}\)\s?\d{3}-\d{4}$', telefono):
        raise ValueError('Formato de teléfono inválido')
    return True

@cxc_bp.route('/clientes/<int:id>', methods=['PUT'])
@login_required
def actualizar_cliente(id):
    cliente = ClienteCxc.query.get_or_404(id)
    data = request.json
    for key, value in data.items():
        setattr(cliente, key, value)
    db.session.commit()
    return jsonify(cliente.to_dict())

@cxc_bp.route('/clientes/<int:id>', methods=['DELETE'])
@login_required
def eliminar_cliente(id):
    cliente = ClienteCxc.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return '', 204

@cxc_bp.route('/clientes/<int:id>/transacciones', methods=['GET'])
@login_required
def get_transacciones_cliente(id):
    cliente = ClienteCxc.query.get_or_404(id)
    transacciones = []
    for cuenta in cliente.cuentas_por_cobrar:
        transacciones.extend(cuenta.to_dict()['transacciones'])
    return jsonify(transacciones)

@cxc_bp.route('/analisis-clientes', methods=['GET'])
@login_required
def analisis_clientes():
    try:
        # Métricas básicas
        total_clientes = ClienteCxc.query.count()
        
        # Análisis de ventas
        cuentas = CuentaPorCobrar.query.all()
        ventas_totales = sum(cuenta.monto for cuenta in cuentas) if cuentas else 0
        
        # Ventas por mes (últimos 6 meses)
        fecha_inicio = datetime.now() - timedelta(days=180)
        ventas_mensuales = db.session.query(
            func.date_trunc('month', CuentaPorCobrar.fecha_emision).label('mes'),
            func.sum(CuentaPorCobrar.monto).label('total')
        ).filter(CuentaPorCobrar.fecha_emision >= fecha_inicio)\
         .group_by('mes')\
         .order_by('mes').all()
        
        # Top 5 clientes
        top_clientes = db.session.query(
            ClienteCxc.nombre,
            func.sum(CuentaPorCobrar.monto).label('total_ventas')
        ).join(CuentaPorCobrar)\
         .group_by(ClienteCxc.nombre)\
         .order_by(text('total_ventas DESC'))\
         .limit(5).all()
        
        # Estado de cuentas por fecha de vencimiento
        hoy = datetime.now().date()
        estado_cuentas = {
            'al_dia': 0,
            'vencidas': 0,
            'total_vencido': 0
        }
        
        if cuentas:
            for cuenta in cuentas:
                if cuenta.fecha_vencimiento >= hoy:
                    estado_cuentas['al_dia'] += 1
                else:
                    estado_cuentas['vencidas'] += 1
                    estado_cuentas['total_vencido'] += cuenta.monto
        
        return jsonify({
            'metricas_basicas': {
                'total_clientes': total_clientes,
                'total_cuentas': len(cuentas) if cuentas else 0,
                'ventas_totales': float(ventas_totales),
                'promedio_venta': float(ventas_totales/len(cuentas)) if cuentas and len(cuentas) > 0 else 0
            },
            'ventas_mensuales': [
                {
                    'mes': mes.strftime('%Y-%m'),
                    'total': float(total)
                } for mes, total in ventas_mensuales
            ],
            'top_clientes': [
                {
                    'nombre': nombre,
                    'total_ventas': float(total)
                } for nombre, total in top_clientes
            ],
            'estado_cuentas': {
                'al_dia': estado_cuentas['al_dia'],
                'vencidas': estado_cuentas['vencidas'],
                'total_vencido': float(estado_cuentas['total_vencido'])
            }
        })
    except Exception as e:
        print(f"Error en análisis de clientes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@cxc_bp.route('/tipos-cliente', methods=['GET'])
@login_required
def get_tipos_cliente():
    tipos = TipoCliente.query.all()
    return jsonify([tipo.to_dict() for tipo in tipos])

@cxc_bp.route('/tipos-cliente', methods=['POST'])
@login_required
def crear_tipo_cliente():
    data = request.json
    nuevo_tipo = TipoCliente(nombre=data['nombre'])
    db.session.add(nuevo_tipo)
    db.session.commit()
    return jsonify(nuevo_tipo.to_dict()), 201

@cxc_bp.route('/cuentas-por-cobrar', methods=['GET'])
@login_required
def get_cuentas_por_cobrar():
    cuentas = CuentaPorCobrar.query.all()
    return jsonify([cuenta.to_dict() for cuenta in cuentas])

@cxc_bp.route('/cuentas-por-cobrar', methods=['POST'])
@login_required
def crear_cuenta_por_cobrar():
    data = request.json
    nueva_cuenta = CuentaPorCobrar(
        cliente_id=data['cliente_id'],
        monto=data['monto'],
        fecha_emision=datetime.strptime(data['fecha_emision'], '%Y-%m-%d').date(),
        fecha_vencimiento=datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%d').date(),
        estado=data['estado']
    )
    db.session.add(nueva_cuenta)
    db.session.commit()
    return jsonify(nueva_cuenta.to_dict()), 201

@cxc_bp.route('/descuentos-devoluciones', methods=['GET'])
@login_required
def get_descuentos_devoluciones():
    descuentos_devoluciones = DescuentoDevolucion.query.all()
    return jsonify([dd.to_dict() for dd in descuentos_devoluciones])

@cxc_bp.route('/descuentos-devoluciones', methods=['POST'])
@login_required
def crear_descuento_devolucion():
    data = request.json
    nuevo_dd = DescuentoDevolucion(
        cuenta_por_cobrar_id=data['cuenta_por_cobrar_id'],
        tipo=data['tipo'],
        monto=data['monto'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    )
    db.session.add(nuevo_dd)
    db.session.commit()
    return jsonify(nuevo_dd.to_dict()), 201

@cxc_bp.route('/notas-credito', methods=['GET'])
@login_required
def get_notas_credito():
    notas_credito = NotaCreditoCxc.query.all()
    return jsonify([nc.to_dict() for nc in notas_credito])

@cxc_bp.route('/notas-credito', methods=['POST'])
@login_required
def crear_nota_credito():
    data = request.json
    nueva_nc = NotaCreditoCxc(
        cuenta_por_cobrar_id=data['cuenta_por_cobrar_id'],
        monto=data['monto'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
        motivo=data['motivo']
    )
    db.session.add(nueva_nc)
    db.session.commit()
    return jsonify(nueva_nc.to_dict()), 201

@cxc_bp.route('/notas-debito', methods=['GET'])
@login_required
def get_notas_debito():
    notas_debito = NotaDebitoCxc.query.all()
    return jsonify([nd.to_dict() for nd in notas_debito])

@cxc_bp.route('/notas-debito', methods=['POST'])
@login_required
def crear_nota_debito():
    data = request.json
    nueva_nd = NotaDebitoCxc(
        cuenta_por_cobrar_id=data['cuenta_por_cobrar_id'],
        monto=data['monto'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
        motivo=data['motivo']
    )
    db.session.add(nueva_nd)
    db.session.commit()
    return jsonify(nueva_nd.to_dict()), 201

@cxc_bp.route('/recibos', methods=['GET'])
@login_required
def get_recibos():
    recibos = Recibo.query.all()
    return jsonify([recibo.to_dict() for recibo in recibos])

@cxc_bp.route('/recibos', methods=['POST'])
@login_required
def crear_recibo():
    data = request.json
    nuevo_recibo = Recibo(
        cuenta_por_cobrar_id=data['cuenta_por_cobrar_id'],
        monto=data['monto'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    )
    db.session.add(nuevo_recibo)
    db.session.commit()
    return jsonify(nuevo_recibo.to_dict()), 201

@cxc_bp.route('/anticipos', methods=['GET'])
@login_required
def get_anticipos():
    anticipos = AnticipoCxC.query.all()
    return jsonify([anticipo.to_dict() for anticipo in anticipos])

@cxc_bp.route('/anticipos', methods=['POST'])
@login_required
def crear_anticipo():
    data = request.json
    nuevo_anticipo = AnticipoCxC(
        cliente_id=data['cliente_id'],
        monto=data['monto'],
        fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date()
    )
    db.session.add(nuevo_anticipo)
    db.session.commit()
    return jsonify(nuevo_anticipo.to_dict()), 201

@cxc_bp.route('/condiciones-pago', methods=['GET'])
@login_required
def get_condiciones_pago():
    condiciones = CondicionPago.query.all()
    return jsonify([condicion.to_dict() for condicion in condiciones])

@cxc_bp.route('/condiciones-pago', methods=['POST'])
@login_required
def crear_condicion_pago():
    data = request.json
    nueva_condicion = CondicionPago(
        nombre=data['nombre'],
        dias=data['dias']
    )
    db.session.add(nueva_condicion)
    db.session.commit()
    return jsonify(nueva_condicion.to_dict()), 201