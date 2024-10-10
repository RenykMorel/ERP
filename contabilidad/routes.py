from flask import render_template, request, jsonify, abort
from . import contabilidad_bp
from .models import ContabilidadCuenta, AsientoDiario, MayorGeneral, BalanzaComprobacion, EstadoResultados, BalanceGeneral, Configuraciones, FlujoCaja
from app import db
from datetime import datetime

@contabilidad_bp.route('/balanza_comprobacion', methods=['GET'])
def balanza_comprobacion():
    return render_template('contabilidad/balanza_comprobacion.html')

@contabilidad_bp.route('/balanza_comprobacion/generar', methods=['POST'])
def generar_balanza_comprobacion():
    fecha_corte = datetime.strptime(request.json['fecha_corte'], '%Y-%m-%d')
    cuentas = ContabilidadCuenta.query.all()
    balanza = []
    for cuenta in cuentas:
        saldos = BalanzaComprobacion.query.filter(
            BalanzaComprobacion.cuenta_id == cuenta.id,
            BalanzaComprobacion.fecha <= fecha_corte
        ).order_by(BalanzaComprobacion.fecha.desc()).first()
        
        if saldos:
            balanza.append({
                'cuenta': cuenta.nombre,
                'debe': saldos.debe,
                'haber': saldos.haber,
                'saldo_deudor': max(saldos.debe - saldos.haber, 0),
                'saldo_acreedor': max(saldos.haber - saldos.debe, 0)
            })

    return jsonify(balanza)

@contabilidad_bp.route('/estado_resultados', methods=['GET'])
def estado_resultados():
    return render_template('contabilidad/estado_resultados.html')

@contabilidad_bp.route('/estado_resultados/generar', methods=['POST'])
def generar_estado_resultados():
    fecha_inicio = datetime.strptime(request.json['fecha_inicio'], '%Y-%m-%d')
    fecha_fin = datetime.strptime(request.json['fecha_fin'], '%Y-%m-%d')
    
    # Aquí iría la lógica para calcular el estado de resultados
    # Por ahora, usaremos datos de ejemplo
    ingresos = db.session.query(db.func.sum(EstadoResultados.monto)).filter(
        EstadoResultados.tipo == 'ingreso',
        EstadoResultados.fecha.between(fecha_inicio, fecha_fin)
    ).scalar() or 0

    gastos = db.session.query(db.func.sum(EstadoResultados.monto)).filter(
        EstadoResultados.tipo == 'gasto',
        EstadoResultados.fecha.between(fecha_inicio, fecha_fin)
    ).scalar() or 0

    utilidad = ingresos - gastos

    return jsonify({
        'ingresos': ingresos,
        'gastos': gastos,
        'utilidad': utilidad
    })

@contabilidad_bp.route('/balance_general', methods=['GET'])
def balance_general():
    return render_template('contabilidad/balance_general.html')

@contabilidad_bp.route('/balance_general/generar', methods=['POST'])
def generar_balance_general():
    fecha_balance = datetime.strptime(request.json['fecha_balance'], '%Y-%m-%d')
    
    # Aquí iría la lógica para calcular el balance general
    # Por ahora, usaremos datos de ejemplo
    activos = db.session.query(db.func.sum(BalanceGeneral.monto)).filter(
        BalanceGeneral.tipo == 'activo',
        BalanceGeneral.fecha <= fecha_balance
    ).scalar() or 0

    pasivos = db.session.query(db.func.sum(BalanceGeneral.monto)).filter(
        BalanceGeneral.tipo == 'pasivo',
        BalanceGeneral.fecha <= fecha_balance
    ).scalar() or 0

    capital = activos - pasivos

    return jsonify({
        'activos': {
            'circulante': activos * 0.4,  # Ejemplo: 40% de los activos son circulantes
            'fijo': activos * 0.6,  # Ejemplo: 60% de los activos son fijos
        },
        'pasivos': {
            'corto_plazo': pasivos * 0.3,  # Ejemplo: 30% de los pasivos son a corto plazo
            'largo_plazo': pasivos * 0.7,  # Ejemplo: 70% de los pasivos son a largo plazo
        },
        'capital': capital
    })

@contabilidad_bp.route('/configuraciones', methods=['GET', 'POST'])
def configuraciones():
    if request.method == 'POST':
        data = request.json
        for key, value in data.items():
            config = Configuraciones.query.filter_by(clave=key).first()
            if config:
                config.valor = value
            else:
                new_config = Configuraciones(clave=key, valor=value)
                db.session.add(new_config)
        db.session.commit()
        return jsonify({"message": "Configuraciones actualizadas con éxito"})
    else:
        configs = Configuraciones.query.all()
        return render_template('contabilidad/configuraciones.html', configs=configs)

@contabilidad_bp.route('/mayor_general', methods=['GET'])
def mayor_general():
    return render_template('contabilidad/mayor_general.html')

@contabilidad_bp.route('/mayor_general/listar', methods=['GET'])
def listar_mayor_general():
    cuentas = ContabilidadCuenta.query.all()
    mayor_general = []
    for cuenta in cuentas:
        movimientos = MayorGeneral.query.filter_by(cuenta_id=cuenta.id).order_by(MayorGeneral.fecha).all()
        mayor_general.append({
            'cuenta': cuenta.nombre,
            'movimientos': [{
                'fecha': m.fecha.strftime('%Y-%m-%d'),
                'descripcion': m.descripcion,
                'debe': m.debe,
                'haber': m.haber,
                'saldo': m.saldo
            } for m in movimientos]
        })
    return jsonify(mayor_general)

@contabilidad_bp.route('/mayor_general/cuenta/<int:cuenta_id>', methods=['GET'])
def mayor_general_cuenta(cuenta_id):
    cuenta = ContabilidadCuenta.query.get_or_404(cuenta_id)
    movimientos = MayorGeneral.query.filter_by(cuenta_id=cuenta_id).order_by(MayorGeneral.fecha).all()
    return jsonify({
        'cuenta': cuenta.nombre,
        'movimientos': [{
            'fecha': m.fecha.strftime('%Y-%m-%d'),
            'descripcion': m.descripcion,
            'debe': m.debe,
            'haber': m.haber,
            'saldo': m.saldo
        } for m in movimientos]
    })

@contabilidad_bp.route('/flujo_caja', methods=['GET'])
def flujo_caja():
    return render_template('contabilidad/flujo_caja.html')

@contabilidad_bp.route('/flujo_caja/generar', methods=['POST'])
def generar_flujo_caja():
    fecha_inicio = datetime.strptime(request.json['fecha_inicio'], '%Y-%m-%d')
    fecha_fin = datetime.strptime(request.json['fecha_fin'], '%Y-%m-%d')
    
    ingresos = FlujoCaja.query.filter(
        FlujoCaja.fecha.between(fecha_inicio, fecha_fin),
        FlujoCaja.tipo == 'ingreso'
    ).all()
    
    egresos = FlujoCaja.query.filter(
        FlujoCaja.fecha.between(fecha_inicio, fecha_fin),
        FlujoCaja.tipo == 'egreso'
    ).all()
    
    saldo_inicial = FlujoCaja.query.filter(FlujoCaja.fecha < fecha_inicio).with_entities(db.func.sum(FlujoCaja.monto)).scalar() or 0
    
    return jsonify({
        'ingresos': [{'concepto': i.concepto, 'monto': i.monto} for i in ingresos],
        'egresos': [{'concepto': e.concepto, 'monto': e.monto} for e in egresos],
        'saldo_inicial': saldo_inicial,
        'saldo_final': saldo_inicial + sum(i.monto for i in ingresos) - sum(e.monto for e in egresos)
    })

@contabilidad_bp.route('/cuentas')
def lista_cuentas():
    return render_template('contabilidad/cuentas.html')

@contabilidad_bp.route('/api/cuentas', methods=['GET'])
def api_lista_cuentas():
    cuentas = ContabilidadCuenta.query.all()
    return jsonify([{
        'id': cuenta.id,
        'codigo': cuenta.codigo,
        'nombre': cuenta.nombre,
        'tipo': cuenta.tipo,
        'saldo': cuenta.saldo
    } for cuenta in cuentas])

@contabilidad_bp.route('/cuentas', methods=['POST'])
def crear_cuenta():
    data = request.json
    cuenta = ContabilidadCuenta(**data)
    db.session.add(cuenta)
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cuenta creada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@contabilidad_bp.route('/cuentas/<int:cuenta_id>', methods=['GET'])
def obtener_cuenta(cuenta_id):
    cuenta = ContabilidadCuenta.query.get_or_404(cuenta_id)
    return jsonify({
        'id': cuenta.id,
        'codigo': cuenta.codigo,
        'nombre': cuenta.nombre,
        'tipo': cuenta.tipo,
        'saldo': cuenta.saldo
    })

@contabilidad_bp.route('/cuentas/<int:cuenta_id>', methods=['PUT'])
def actualizar_cuenta(cuenta_id):
    cuenta = ContabilidadCuenta.query.get_or_404(cuenta_id)
    data = request.json
    for key, value in data.items():
        setattr(cuenta, key, value)
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cuenta actualizada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@contabilidad_bp.route('/cuentas/<int:cuenta_id>', methods=['DELETE'])
def eliminar_cuenta(cuenta_id):
    cuenta = ContabilidadCuenta.query.get_or_404(cuenta_id)
    try:
        db.session.delete(cuenta)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cuenta eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@contabilidad_bp.route('/diario', methods=['GET', 'POST'])
def diario():
    if request.method == 'GET':
        return render_template('contabilidad/diario.html')
    elif request.method == 'POST':
        data = request.json
        nuevo_asiento = AsientoDiario(
            fecha=data['fecha'],
            descripcion=data['descripcion'],
            cuenta_id=data['cuenta_id'],
            debe=data['debe'],
            haber=data['haber']
        )
        db.session.add(nuevo_asiento)
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Asiento creado exitosamente'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

@contabilidad_bp.route('/diario/listar', methods=['GET'])
def listar_asientos():
    asientos = AsientoDiario.query.order_by(AsientoDiario.fecha.desc()).all()
    return jsonify([{
        'id': asiento.id,
        'fecha': asiento.fecha.strftime('%Y-%m-%d'),
        'descripcion': asiento.descripcion,
        'cuenta': asiento.cuenta.nombre,
        'debe': asiento.debe,
        'haber': asiento.haber
    } for asiento in asientos])

@contabilidad_bp.route('/asientos', methods=['GET', 'POST'])
def manejar_asientos():
    if request.method == 'POST':
        data = request.json
        nuevo_asiento = AsientoDiario(
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d'),
            descripcion=data['descripcion'],
            cuenta_id=data['cuenta_id'],
            debe=data['debe'],
            haber=data['haber']
        )
        db.session.add(nuevo_asiento)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Asiento creado exitosamente'})
    else:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        asientos = AsientoDiario.query.order_by(AsientoDiario.fecha.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'asientos': [{
                'id': asiento.id,
                'fecha': asiento.fecha.strftime('%Y-%m-%d'),
                'descripcion': asiento.descripcion,
                'cuenta': asiento.cuenta.nombre,
                'debe': asiento.debe,
                'haber': asiento.haber
            } for asiento in asientos.items],
            'total': asientos.total,
            'pages': asientos.pages,
            'current_page': page
        })

@contabilidad_bp.route('/cuentas/buscar')
def buscar_cuentas():
    query = request.args.get('q', '')
    tipo = request.args.get('tipo', '')
    cuentas = ContabilidadCuenta.query
    if query:
        cuentas = cuentas.filter(ContabilidadCuenta.nombre.ilike(f'%{query}%'))
    if tipo:
        cuentas = cuentas.filter_by(tipo=tipo)
    return jsonify([{
        'id': cuenta.id,
        'codigo': cuenta.codigo,
        'nombre': cuenta.nombre,
        'tipo': cuenta.tipo,
        'saldo': cuenta.saldo
    } for cuenta in cuentas.all()])

@contabilidad_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404

@contabilidad_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Error interno del servidor'}), 500