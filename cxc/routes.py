from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required
from cxc.models import ClienteCxc, TipoCliente, CuentaPorCobrar, DescuentoDevolucion, NotaCreditoCxc, NotaDebitoCxc, Recibo, AnticipoCxC, CondicionPago
from app import db

cxc_bp = Blueprint('cxc', __name__, url_prefix='/cxc')

@cxc_bp.route('/clientes', methods=['GET'])
@login_required
def clientes():
    # Obtener todos los clientes de la base de datos
    clientes = ClienteCxc.query.all()
    return render_template('cxc/clientes.html', clientes=clientes)
@cxc_bp.route('/crear-cliente', methods=['GET', 'POST'])
@login_required
def crear_cliente():
    if request.method == 'POST':
        # Lógica para crear un nuevo cliente
        nuevo_cliente = ClienteCxc(
            nombre=request.form['nombre'],
            direccion=request.form['direccion'],
            telefono=request.form['telefono'],
            email=request.form['email']
        )
        db.session.add(nuevo_cliente)
        db.session.commit()
        return redirect(url_for('cxc.clientes'))  # Redirigir a la lista de clientes
    return render_template('cxc/crear_cliente.html')  # Renderizar formulario de creación de cliente


@cxc_bp.route('/eliminar-cliente/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    cliente = ClienteCxc.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for('cxc.clientes'))

@cxc_bp.route('/descuentos-devoluciones')
@login_required
def descuentos_devoluciones():
    descuentos_devoluciones = DescuentoDevolucion.query.all()
    return render_template('cxc/descuentos_devoluciones.html', descuentos_devoluciones=descuentos_devoluciones)

@cxc_bp.route('/crear-descuento-devolucion', methods=['GET', 'POST'])
@login_required
def crear_descuento_devolucion():
    if request.method == 'POST':
        # Lógica para guardar el nuevo descuento o devolución
        nuevo_dd = DescuentoDevolucion(
            tipo=request.form['tipo'],
            monto=request.form['monto'],
            fecha=request.form['fecha'],
            cuenta_por_cobrar_id=request.form['cuenta_por_cobrar_id']
        )
        # Guarda el descuento o devolución en la base de datos
        db.session.add(nuevo_dd)
        db.session.commit()
        return redirect(url_for('cxc.descuentos_devoluciones'))
    return render_template('cxc/crear_descuento_devolucion.html')

@cxc_bp.route('/notas-credito')
@login_required
def notas_credito():
    notas_credito = NotaCreditoCxc.query.all()
    return render_template('cxc/notas_credito.html', notas_credito=notas_credito)

@cxc_bp.route('/crear-nota-credito', methods=['GET', 'POST'])
@login_required
def crear_nota_credito():
    if request.method == 'POST':
        nueva_nota = NotaCreditoCxc(
            monto=request.form['monto'],
            fecha=request.form['fecha'],
            motivo=request.form['motivo'],
            cuenta_por_cobrar_id=request.form['cuenta_por_cobrar_id']
        )
        db.session.add(nueva_nota)
        db.session.commit()
        return redirect(url_for('cxc.notas_credito'))
    return render_template('cxc/crear_nota_credito.html')

@cxc_bp.route('/notas-debito')
@login_required
def notas_debito():
    notas_debito = NotaDebitoCxc.query.all()
    return render_template('cxc/notas_debito.html', notas_debito=notas_debito)

@cxc_bp.route('/crear-nota-debito', methods=['GET', 'POST'])
@login_required
def crear_nota_debito():
    if request.method == 'POST':
        # Lógica para crear una nota de débito
        pass
    return render_template('cxc/crear_nota_debito.html')

@cxc_bp.route('/recibos')
@login_required
def recibos():
    recibos = Recibo.query.all()
    return render_template('cxc/recibos.html', recibos=recibos)

@cxc_bp.route('/crear-recibo', methods=['GET', 'POST'])
@login_required
def crear_recibo():
    if request.method == 'POST':
        # Lógica para crear un nuevo recibo
        pass
    return render_template('cxc/crear_recibo.html')


@cxc_bp.route('/anticipos')
@login_required
def anticipos():
    anticipos = AnticipoCxC.query.all()
    return render_template('cxc/anticipos.html', anticipos=anticipos)

@cxc_bp.route('/crear-anticipo', methods=['GET', 'POST'])
@login_required
def crear_anticipo():
    if request.method == 'POST':
        # Lógica para guardar el nuevo anticipo
        nuevo_anticipo = AnticipoCxC(
            cliente_id=request.form['cliente_id'],
            monto=request.form['monto'],
            fecha=request.form['fecha']
        )
        # Guarda el anticipo en la base de datos
        db.session.add(nuevo_anticipo)
        db.session.commit()
        return redirect(url_for('cxc.anticipos'))
    return render_template('cxc/crear_anticipo.html')

@cxc_bp.route('/condiciones-pago')
@login_required
def condiciones_pago():
    condiciones = CondicionPago.query.all()
    return render_template('cxc/condiciones_pago.html', condiciones=condiciones)

@cxc_bp.route('/crear-condicion-pago', methods=['GET', 'POST'])
@login_required
def crear_condicion_pago():
    if request.method == 'POST':
        # Lógica para crear una nueva condición de pago
        pass
    return render_template('cxc/crear_condicion_pago.html')

@cxc_bp.route('/reporte')
@login_required
def reporte():
    cuentas = CuentaPorCobrar.query.all()
    return render_template('cxc/reporte.html', cuentas=cuentas)

@cxc_bp.route('/tipos-cliente')
@login_required
def tipos_cliente():
    tipos = TipoCliente.query.all()
    return render_template('cxc/tipos_cliente.html', tipos=tipos)

@cxc_bp.route('/crear-tipo-cliente', methods=['GET', 'POST'])
@login_required
def crear_tipo_cliente():
    if request.method == 'POST':
        # Lógica para crear un nuevo tipo de cliente
        pass
    return render_template('cxc/crear_tipo_cliente.html')