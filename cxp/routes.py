from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from extensions import db
from .models import FacturaSuplidor, NotaCreditoCxp, NotaDebitoCxp, OrdenCompra, Suplidor, AnticipoCxP, PagoContado, ReporteCxP, RequisicionCotizacion, SolicitudCompra, TipoSuplidor
import logging

cxp_bp = Blueprint('cxp', __name__, url_prefix='/cxp')

logger = logging.getLogger(__name__)

@cxp_bp.route('/factura-suplidor')
@login_required
def factura_suplidor():
    try:
        facturas = FacturaSuplidor.query.all()
        return render_template('cxp/factura_suplidor.html', facturas=facturas)
    except Exception as e:
        logger.error(f"Error al cargar la página de facturas de suplidor: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/nota-credito')
@login_required
def nota_credito():
    try:
        notas = NotaCreditoCxp.query.all()
        return render_template('cxp/nota_credito.html', notas=notas)
    except Exception as e:
        logger.error(f"Error al cargar la página de notas de crédito: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/nota-debito')
@login_required
def nota_debito():
    try:
        notas = NotaDebitoCxp.query.all()
        return render_template('cxp/nota_debito.html', notas=notas)
    except Exception as e:
        logger.error(f"Error al cargar la página de notas de débito: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/orden-compras')
@login_required
def orden_compras():
    try:
        ordenes = OrdenCompra.query.all()
        return render_template('cxp/orden_compras.html', ordenes=ordenes)
    except Exception as e:
        logger.error(f"Error al cargar la página de órdenes de compra: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/suplidor')
@login_required
def suplidor():
    try:
        suplidores = Suplidor.query.all()
        return render_template('cxp/suplidor.html', suplidores=suplidores)
    except Exception as e:
        logger.error(f"Error al cargar la página de suplidores: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/anticipo-cxp')
@login_required
def anticipo_cxp():
    try:
        anticipos = AnticipoCxP.query.all()
        return render_template('cxp/anticipo_cxp.html', anticipos=anticipos)
    except Exception as e:
        logger.error(f"Error al cargar la página de anticipos CxP: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/pago-contado')
@login_required
def pago_contado():
    try:
        pagos = PagoContado.query.all()
        return render_template('cxp/pago_contado.html', pagos=pagos)
    except Exception as e:
        logger.error(f"Error al cargar la página de pagos de contado: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/reporte-cxp')
@login_required
def reporte_cxp():
    try:
        reportes = ReporteCxP.query.all()
        return render_template('cxp/reporte_cxp.html', reportes=reportes)
    except Exception as e:
        logger.error(f"Error al cargar la página de reportes CxP: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/requisicion-cotizacion')
@login_required
def requisicion_cotizacion():
    try:
        requisiciones = RequisicionCotizacion.query.all()
        return render_template('cxp/requisicion_cotizacion.html', requisiciones=requisiciones)
    except Exception as e:
        logger.error(f"Error al cargar la página de requisiciones de cotización: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/solicitud-compras')
@login_required
def solicitud_compras():
    try:
        solicitudes = SolicitudCompra.query.all()
        return render_template('cxp/solicitud_compras.html', solicitudes=solicitudes)
    except Exception as e:
        logger.error(f"Error al cargar la página de solicitudes de compra: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cxp_bp.route('/tipo-suplidor')
@login_required
def tipo_suplidor():
    try:
        tipos = TipoSuplidor.query.all()
        return render_template('cxp/tipo_suplidor.html', tipos=tipos)
    except Exception as e:
        logger.error(f"Error al cargar la página de tipos de suplidor: {str(e)}")
        return jsonify({"error": str(e)}), 500