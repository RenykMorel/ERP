from flask import jsonify, request, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from . import banco_bp
from .banco_models import NuevoBanco, Deposito, NotaCreditoDebito, Transferencia, Conciliacion, CuentaAfectada, Divisa
from extensions import db
import logging
from datetime import datetime
from flask import current_app
from sqlalchemy import or_, func
from .banco_models import CuentaBancaria


logger = logging.getLogger(__name__)

# Rutas para Bancos
@banco_bp.route("/bancos")
@banco_bp.route("/Bancos")
@login_required
def sub_bancos():
    try:
        bancos = NuevoBanco.query.all()
        return render_template('banco/sub_bancos.html', bancos=bancos)
    except Exception as e:
        logger.error(f"Error al cargar la página de bancos: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de bancos: {str(e)}"}), 500

@banco_bp.route("/obtener-banco/<int:id>")
@login_required
def obtener_banco(id):
    try:
        banco = NuevoBanco.query.get_or_404(id)
        return jsonify(banco.to_dict())
    except Exception as e:
        logger.error(f"Error al obtener banco: {str(e)}")
        return jsonify({"error": f"Error al obtener banco: {str(e)}"}), 500

@banco_bp.route("/actualizar-banco/<int:id>", methods=["PUT"])
@login_required
def actualizar_banco(id):
    banco = NuevoBanco.query.get_or_404(id)
    datos = request.json
    campos_actualizables = ["nombre", "telefono", "contacto", "telefono_contacto", "estatus", "direccion", "codigo", "codigo_swift"]
    
    try:
        for key, value in datos.items():
            if key in campos_actualizables and value != getattr(banco, key):
                if key in ["nombre", "telefono"]:
                    existing = NuevoBanco.query.filter(NuevoBanco.id != id, getattr(NuevoBanco, key) == value).first()
                    if existing:
                        return jsonify({"error": f"Ya existe un banco con ese {key}"}), 400
                setattr(banco, key, value)
        
        db.session.commit()
        logger.info(f"Banco actualizado: {banco.nombre}")
        return jsonify(banco.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar banco: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/eliminar-banco/<int:id>", methods=["DELETE"])
@login_required
def eliminar_banco(id):
    banco = NuevoBanco.query.get_or_404(id)
    try:
        db.session.delete(banco)
        db.session.commit()
        logger.info(f"Banco eliminado: {banco.nombre}")
        return jsonify({"message": "Banco eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar banco: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/cambiar-estatus-banco/<int:id>", methods=["PUT"])
@login_required
def cambiar_estatus_banco(id):
    banco = NuevoBanco.query.get_or_404(id)
    datos = request.json
    try:
        banco.estatus = datos["estatus"]
        db.session.commit()
        logger.info(f"Estatus del banco {banco.nombre} cambiado a {banco.estatus}")
        return jsonify(banco.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al cambiar estatus del banco: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/buscar-bancos")
@login_required
def buscar_bancos():
    try:
        query = NuevoBanco.query
        if request.args.get("id"):
            query = query.filter(NuevoBanco.id == request.args.get("id"))
        if request.args.get("nombre"):
            query = query.filter(NuevoBanco.nombre.ilike(f"%{request.args.get('nombre')}%"))
        if request.args.get("contacto"):
            query = query.filter(NuevoBanco.contacto.ilike(f"%{request.args.get('contacto')}%"))
        if request.args.get("estatus"):
            query = query.filter(NuevoBanco.estatus == request.args.get("estatus"))

        bancos = query.all()
        logger.info(f"Búsqueda de bancos realizada. Resultados: {len(bancos)}")
        return jsonify([banco.to_dict() for banco in bancos])
    except Exception as e:
        logger.error(f"Error en buscar_bancos: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@banco_bp.route("/crear-banco", methods=["POST"])
@login_required
def crear_banco():
    datos = request.json
    logger.info(f"Datos recibidos para crear banco: {datos}")
    
    required_fields = ['nombre', 'telefono']
    for field in required_fields:
        if not datos.get(field):
            logger.warning(f"Campo requerido faltante: {field}")
            return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

    try:
        nuevo_banco = NuevoBanco(
            nombre=datos['nombre'],
            telefono=datos['telefono'],
            contacto=datos.get('contacto', ''),
            telefono_contacto=datos.get('telefono_contacto', ''),
            estatus=datos.get('estatus', 'activo'),
            direccion=datos.get('direccion', ''),
            codigo=datos.get('codigo', ''),
            codigo_swift=datos.get('codigo_swift', ''),
            fecha=datetime.now()
        )
        logger.info(f"Objeto NuevoBanco creado: {vars(nuevo_banco)}")
        db.session.add(nuevo_banco)
        db.session.commit()
        logger.info(f"Nuevo banco creado: {nuevo_banco.nombre}")

        # Notificar al asistente virtual
        asistente = current_app.asistente
        mensaje_asistente = (f"Se ha creado un nuevo banco con los siguientes detalles:\n"
                             f"Nombre: {nuevo_banco.nombre}\n"
                             f"Teléfono: {nuevo_banco.telefono}\n"
                             f"Contacto: {nuevo_banco.contacto}\n"
                             f"Teléfono de contacto: {nuevo_banco.telefono_contacto}\n"
                             f"Estatus: {nuevo_banco.estatus}\n"
                             f"Dirección: {nuevo_banco.direccion}\n"
                             f"Código: {nuevo_banco.codigo}\n"
                             f"Código SWIFT: {nuevo_banco.codigo_swift}\n"
                             f"Fecha de creación: {nuevo_banco.fecha}")
        respuesta_asistente = asistente.responder(mensaje_asistente, current_user.id)

        return jsonify({
            "message": "Banco creado exitosamente",
            "banco": nuevo_banco.to_dict(),
            "asistente_respuesta": respuesta_asistente['contenido'] if isinstance(respuesta_asistente, dict) else str(respuesta_asistente)
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        error_info = str(e.orig)
        logger.error(f"IntegrityError al crear banco: {error_info}")
        error_details = {}
        if 'unique constraint' in error_info.lower():
            if 'nuevo_bancos_nombre_key' in error_info:
                error_details['nombre'] = "Ya existe un banco con este nombre."
            elif 'nuevo_bancos_telefono_key' in error_info:
                error_details['telefono'] = "Ya existe un banco con este número de teléfono."
            else:
                error_details['general'] = "Ya existe un banco con información duplicada."
        else:
            error_details['general'] = "Error de integridad al crear el banco."
        
        logger.warning(f"Error al crear banco: {error_details} Detalles: {datos}")
        return jsonify({"error": "Error al crear el banco", "details": error_details}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error inesperado al crear banco: {str(e)}")
        return jsonify({"error": f"Error inesperado al crear el banco: {str(e)}"}), 500
    
@banco_bp.route("/obtener-divisas-activas", methods=["GET"])
@login_required
def obtener_divisas_activas():
    try:
        divisas = Divisa.query.filter_by(estatus='activo').all()
        return jsonify([{
            'id': divisa.id,
            'codigo': divisa.codigo,
            'nombre': divisa.nombre,
            'simbolo': divisa.simbolo
        } for divisa in divisas])
    except Exception as e:
        logger.error(f"Error al obtener divisas activas: {str(e)}")
        return jsonify({"error": "Error al obtener divisas"}), 500 
        

@banco_bp.route("/crear-deposito", methods=["POST"])
@login_required
def crear_deposito():
    datos = request.json
    logger.info(f"Datos recibidos para crear depósito: {datos}")
    
    required_fields = ['monto', 'fecha', 'banco_id', 'divisa_id', 'cuenta_bancaria', 'numero', 'concepto', 'estatus', 'referencia']
    for field in required_fields:
        if not datos.get(field):
            logger.warning(f"Campo requerido faltante: {field}")
            return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

    try:
        nuevo_deposito = Deposito(
            monto=datos['monto'],
            fecha=datetime.fromisoformat(datos['fecha']),
            banco_id=datos['banco_id'],
            divisa_id=datos['divisa_id'],
            cuenta_bancaria=datos['cuenta_bancaria'],
            numero=datos['numero'],
            concepto=datos['concepto'],
            estatus=datos['estatus'],
            referencia=datos['referencia'],
            descripcion=datos.get('descripcion', ''),
            creador=current_user.nombre_usuario,
            actualizado_por=current_user.nombre_usuario,
            fuente=datos.get('fuente', ''),
            fuente_referencia=datos.get('fuente_referencia', '')
        )
        logger.info(f"Objeto Deposito creado: {vars(nuevo_deposito)}")
        db.session.add(nuevo_deposito)

        # Agregar cuentas afectadas
        for cuenta_afectada in datos.get('cuentas_afectadas', []):
            nueva_cuenta_afectada = CuentaAfectada(
                deposito_id=nuevo_deposito.id,
                identificador=cuenta_afectada['identificador'],
                tipo=cuenta_afectada['tipo'],
                monto=cuenta_afectada['monto']
            )
            db.session.add(nueva_cuenta_afectada)

        db.session.commit()
        logger.info(f"Nuevo depósito creado: {nuevo_deposito.id}")

        # Notificar al asistente virtual
        asistente = current_app.asistente
        mensaje_asistente = (f"Se ha creado un nuevo depósito con los siguientes detalles:\n"
                             f"Monto: {nuevo_deposito.monto}\n"
                             f"Fecha: {nuevo_deposito.fecha}\n"
                             f"Banco ID: {nuevo_deposito.banco_id}\n"
                             f"Divisa ID: {nuevo_deposito.divisa_id}\n"
                             f"Cuenta Bancaria: {nuevo_deposito.cuenta_bancaria}\n"
                             f"Número: {nuevo_deposito.numero}\n"
                             f"Concepto: {nuevo_deposito.concepto}\n"
                             f"Estatus: {nuevo_deposito.estatus}\n"
                             f"Referencia: {nuevo_deposito.referencia}")
        respuesta_asistente = asistente.responder(mensaje_asistente, current_user.id)
        logger.info(f"Respuesta del asistente: {respuesta_asistente}")

        return jsonify({
            "message": "Depósito creado exitosamente",
            "deposito": nuevo_deposito.to_dict(),
            "asistente_respuesta": respuesta_asistente['contenido'] if isinstance(respuesta_asistente, dict) else str(respuesta_asistente)
        }), 201
    except ValueError as ve:
        db.session.rollback()
        logger.error(f"Error de validación al crear depósito: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error inesperado al crear depósito: {str(e)}")
        return jsonify({"error": f"Error inesperado al crear el depósito: {str(e)}"}), 500

@banco_bp.route("/obtener-depositos")
@login_required
def obtener_depositos():
    try:
        depositos = Deposito.query.all()
        return jsonify([deposito.to_dict() for deposito in depositos])
    except Exception as e:
        logger.error(f"Error al obtener depósitos: {str(e)}")
        return jsonify({"error": f"Error al obtener depósitos: {str(e)}"}), 500    

@banco_bp.route("/divisas", methods=["GET", "POST"])
@login_required
def listar_crear_divisas():
    if request.method == "GET":
        try:
            logger.info("Iniciando función listar_divisas")
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            codigo = request.args.get('codigo', '')
            nombre = request.args.get('nombre', '')

            logger.info(f"Parámetros recibidos: page={page}, per_page={per_page}, codigo={codigo}, nombre={nombre}")

            query = Divisa.query

            if codigo:
                query = query.filter(Divisa.codigo.ilike(f'%{codigo}%'))
            if nombre:
                query = query.filter(Divisa.nombre.ilike(f'%{nombre}%'))

            divisas_paginadas = query.paginate(page=page, per_page=per_page, error_out=False)
            logger.info(f"Divisas paginadas obtenidas. Total: {divisas_paginadas.total}")

            divisas = [{
                'id': divisa.id,
                'codigo': divisa.codigo,
                'nombre': divisa.nombre,
                'tasa_cambio': divisa.tasa_cambio,
                'fecha_actualizacion': divisa.fecha_actualizacion.isoformat() if divisa.fecha_actualizacion else None,
                'abreviatura': divisa.abreviatura,
                'simbolo': divisa.simbolo,
                'estatus': divisa.estatus
            } for divisa in divisas_paginadas.items]

            logger.info(f"Divisas procesadas: {len(divisas)}")

            response = {
                'divisas': divisas,
                'total': divisas_paginadas.total,
                'pages': divisas_paginadas.pages,
                'page': page,
                'per_page': per_page
            }
            logger.info("Respuesta preparada con éxito")
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error al listar divisas: {str(e)}", exc_info=True)
            return jsonify({"error": "Error interno del servidor al listar divisas", "details": str(e)}), 500

    # ... (el resto del código para el método POST)

    # ... (el resto del código para el método POST)
    elif request.method == "POST":
        datos = request.json
        logger.info(f"Datos recibidos para crear divisa: {datos}")
        
        required_fields = ['nombre', 'tasa_cambio', 'abreviatura', 'simbolo']
        for field in required_fields:
            if not datos.get(field):
                logger.warning(f"Campo requerido faltante: {field}")
                return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

        try:
            if not datos.get('codigo'):
                codigo_generado = datos['nombre'][:3].upper()
                codigo_base = codigo_generado
                contador = 1
                while Divisa.query.filter_by(codigo=codigo_generado).first():
                    codigo_generado = f"{codigo_base}{contador}"
                    contador += 1
                datos['codigo'] = codigo_generado

            # Obtener el máximo ID actual
            max_id = db.session.query(func.max(Divisa.id)).scalar() or 0
            
            # Incrementar el ID para la nueva divisa
            new_id = max_id + 1
            
            nueva_divisa = Divisa(
                id=new_id,
                codigo=datos['codigo'],
                nombre=datos['nombre'],
                tasa_cambio=datos['tasa_cambio'],
                abreviatura=datos['abreviatura'],
                simbolo=datos['simbolo'],
                cuenta_por_cobrar=datos.get('cuenta_por_cobrar', ''),
                cuenta_por_pagar=datos.get('cuenta_por_pagar', ''),
                prima_cxc=datos.get('prima_cxc', ''),
                prima_cxp=datos.get('prima_cxp', ''),
                ganancia_diferencia_cambiaria=datos.get('ganancia_diferencia_cambiaria', ''),
                perdida_diferencia_cambiaria=datos.get('perdida_diferencia_cambiaria', ''),
                anticipo=datos.get('anticipo', ''),
                anticipo_prima=datos.get('anticipo_prima', ''),
                anticipo_cxp=datos.get('anticipo_cxp', ''),
                anticipo_cxp_prima=datos.get('anticipo_cxp_prima', ''),
                caja=datos.get('caja', ''),
                caja_prima=datos.get('caja_prima', ''),
                nota_credito=datos.get('nota_credito', ''),
                nota_credito_prima=datos.get('nota_credito_prima', ''),
                desglose=datos.get('desglose', ''),
                moneda_funcional=datos.get('moneda_funcional', False)
            )
            
            db.session.add(nueva_divisa)
            db.session.commit()
            logger.info(f"Nueva divisa creada: {nueva_divisa.codigo} con ID: {nueva_divisa.id}")

            return jsonify({
                "message": "Divisa creada exitosamente",
                "divisa": nueva_divisa.to_dict()
            }), 201
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"IntegrityError al crear divisa: {str(e)}")
            return jsonify({"error": "Ya existe una divisa con información duplicada."}), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error inesperado al crear divisa: {str(e)}")
            return jsonify({"error": f"Error inesperado al crear la divisa: {str(e)}"}), 500

@banco_bp.route("/obtener-cuentas-bancarias", methods=["GET"])
@login_required
def obtener_cuentas_bancarias():
    try:
        cuentas = CuentaBancaria.query.all()
        return jsonify([cuenta.to_dict() for cuenta in cuentas])
    except Exception as e:
        logger.error(f"Error al obtener cuentas bancarias: {str(e)}")
        return jsonify({"error": "Error al obtener cuentas bancarias"}), 500

@banco_bp.route("/divisas/<int:id>", methods=["GET", "PUT", "DELETE"])
@login_required
def manejar_divisa(id):
    try:
        divisa = Divisa.query.get_or_404(id)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error al obtener la divisa con ID {id}: {str(e)}")
        return jsonify({"error": "Error al obtener la divisa"}), 500

    if request.method == "GET":
        return jsonify(divisa.to_dict())
    
    elif request.method == "PUT":
        datos = request.json
        campos_actualizables = ["nombre", "tasa_cambio", "abreviatura", "simbolo", "cuenta_por_cobrar", "cuenta_por_pagar", 
                                "prima_cxc", "prima_cxp", "ganancia_diferencia_cambiaria", "perdida_diferencia_cambiaria", 
                                "anticipo", "anticipo_prima", "anticipo_cxp", "anticipo_cxp_prima", "caja", "caja_prima", 
                                "nota_credito", "nota_credito_prima", "moneda_funcional", "desglose"]
        
        try:
            for key, value in datos.items():
                if key in campos_actualizables:
                    setattr(divisa, key, value)
            
            divisa.fecha_actualizacion = datetime.now()
            db.session.commit()
            current_app.logger.info(f"Divisa actualizada: {divisa.codigo}")
            return jsonify(divisa.to_dict())
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de integridad al actualizar divisa: {str(e)}")
            return jsonify({"error": "Error de integridad al actualizar la divisa"}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de base de datos al actualizar divisa: {str(e)}")
            return jsonify({"error": "Error de base de datos al actualizar la divisa"}), 500
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al actualizar divisa: {str(e)}")
            return jsonify({"error": "Error inesperado al actualizar la divisa"}), 500
    
    elif request.method == "DELETE":
        try:
            current_app.logger.info(f"Intentando eliminar divisa con ID: {id}")
            current_app.logger.info(f"Detalles de la divisa: {divisa.to_dict()}")

            # Consulta optimizada para contar depósitos
            current_app.logger.info(f"Ejecutando consulta de conteo para divisa_id: {id}")
            depositos_count = db.session.query(func.count(Deposito.id)).filter(Deposito.divisa_id == id).scalar()
            
            current_app.logger.info(f"Conteo de depósitos para divisa {id}: {depositos_count}")
            
            if depositos_count > 0:
                current_app.logger.warning(f"No se puede eliminar la divisa {id} porque tiene {depositos_count} depósitos asociados")
                return jsonify({"error": f"No se puede eliminar la divisa porque existen {depositos_count} depósitos asociados"}), 400
            
            # Aquí puedes agregar verificaciones para otras relaciones si es necesario

            db.session.delete(divisa)
            db.session.commit()
            current_app.logger.info(f"Divisa eliminada: {divisa.codigo}")
            return jsonify({"message": "Divisa eliminada correctamente"})
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de integridad al eliminar divisa: {str(e)}")
            return jsonify({"error": "No se puede eliminar la divisa debido a restricciones de integridad"}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de base de datos al eliminar divisa: {str(e)}")
            return jsonify({"error": f"Error de base de datos al eliminar la divisa: {str(e)}"}), 500
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al eliminar divisa: {str(e)}")
            return jsonify({"error": f"Error inesperado al eliminar la divisa: {str(e)}"}), 500




@banco_bp.route("/eventos", methods=["GET"])
@login_required
def obtener_eventos():
    start = request.args.get('start')
    end = request.args.get('end')
    # Implementa la lógica de eventos aquí.
    return jsonify({"eventos": "Eventos encontrados"})

# Rutas para Notas de Crédito/Débito
@banco_bp.route("/notas-credito-debito")
@login_required
def notas_credito_debito():
    try:
        notas = NotaCreditoDebito.query.all()
        return render_template('banco/notas_credito_debito.html', notas=notas)
    except Exception as e:
        logger.error(f"Error al cargar la página de notas de crédito/débito: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de notas de crédito/débito: {str(e)}"}), 500

# Rutas para Transferencias Bancarias
@banco_bp.route("/transferencias")
@login_required
def transferencias():
    try:
        transferencias = Transferencia.query.all()
        return render_template('banco/transferencias.html', transferencias=transferencias)
    except Exception as e:
        logger.error(f"Error al cargar la página de transferencias: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de transferencias: {str(e)}"}), 500

@banco_bp.route("/gestion-bancos")
@login_required
def gestion_bancos():
    try:
        bancos = NuevoBanco.query.all()
        return render_template('banco/gestion_bancos.html', bancos=bancos)
    except Exception as e:
        logger.error(f"Error al cargar la página de gestión de bancos: {str(e)}")
        return jsonify({"error": f"Error al cargar la página de gestión de bancos: {str(e)}"}), 500

@banco_bp.route("/obtener-bancos")
@login_required
def obtener_bancos():
    try:
        bancos = NuevoBanco.query.all()
        return jsonify([banco.to_dict() for banco in bancos])
    except Exception as e:
        logger.error(f"Error al obtener bancos: {str(e)}")
        return jsonify({"error": f"Error al obtener bancos: {str(e)}"}), 500

@banco_bp.route("/obtener-deposito/<int:id>")
@login_required
def obtener_deposito(id):
    try:
        deposito = Deposito.query.get_or_404(id)
        return jsonify(deposito.to_dict())
    except Exception as e:
        logger.error(f"Error al obtener depósito: {str(e)}")
        return jsonify({"error": f"Error al obtener depósito: {str(e)}"}), 500

@banco_bp.route("/actualizar-deposito/<int:id>", methods=["PUT"])
@login_required
def actualizar_deposito(id):
    deposito = Deposito.query.get_or_404(id)
    datos = request.json
    campos_actualizables = ["monto", "fecha", "banco_id", "divisa_id", "cuenta_bancaria", "numero", "concepto", "estatus", "referencia", "descripcion", "fuente", "fuente_referencia"]
    
    try:
        for key, value in datos.items():
            if key in campos_actualizables:
                if key == "fecha":
                    value = datetime.fromisoformat(value)
                setattr(deposito, key, value)
        
        deposito.actualizado_por = current_user.nombre_usuario

        # Actualizar cuentas afectadas
        CuentaAfectada.query.filter_by(deposito_id=deposito.id).delete()
        for cuenta_afectada in datos.get('cuentas_afectadas', []):
            nueva_cuenta_afectada = CuentaAfectada(
                deposito_id=deposito.id,
                identificador=cuenta_afectada['identificador'],
                tipo=cuenta_afectada['tipo'],
                monto=cuenta_afectada['monto']
            )
            db.session.add(nueva_cuenta_afectada)

        db.session.commit()
        logger.info(f"Depósito actualizado: {deposito.id}")
        return jsonify(deposito.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar depósito: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/eliminar-deposito/<int:id>", methods=["DELETE"])
@login_required
def eliminar_deposito(id):
    deposito = Deposito.query.get_or_404(id)
    try:
        db.session.delete(deposito)
        db.session.commit()
        logger.info(f"Depósito eliminado: {deposito.id}")
        return jsonify({"message": "Depósito eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al eliminar depósito: {str(e)}")
        return jsonify({"error": str(e)}), 500

@banco_bp.route("/crear-nota-credito-debito", methods=["POST"])
@login_required
def crear_nota_credito_debito():
    datos = request.json
    logger.info(f"Datos recibidos para crear nota de crédito/débito: {datos}")
    
    required_fields = ['tipo', 'monto', 'fecha', 'banco_id', 'divisa_id']
    for field in required_fields:
        if not datos.get(field):
            logger.warning(f"Campo requerido faltante: {field}")
            return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

    try:
        nueva_nota = NotaCreditoDebito(
            tipo=datos['tipo'],
            monto=datos['monto'],
            fecha=datetime.fromisoformat(datos['fecha']),
            banco_id=datos['banco_id'],
            divisa_id=datos['divisa_id'],
            descripcion=datos.get('descripcion', '')
        )
        db.session.add(nueva_nota)
        db.session.commit()
        logger.info(f"Nueva nota de crédito/débito creada: {nueva_nota.id}")
        return jsonify({"message": "Nota de crédito/débito creada exitosamente", "nota": nueva_nota.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear nota de crédito/débito: {str(e)}")
        return jsonify({"error": f"Error al crear la nota de crédito/débito: {str(e)}"}), 500

@banco_bp.route("/crear-transferencia", methods=["POST"])
@login_required
def crear_transferencia():
    datos = request.json
    logger.info(f"Datos recibidos para crear transferencia: {datos}")
    
    required_fields = ['monto', 'fecha', 'banco_origen_id', 'banco_destino_id', 'divisa_id']
    for field in required_fields:
        if not datos.get(field):
            logger.warning(f"Campo requerido faltante: {field}")
            return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

    try:
        nueva_transferencia = Transferencia(
            monto=datos['monto'],
            fecha=datetime.fromisoformat(datos['fecha']),
            banco_origen_id=datos['banco_origen_id'],
            banco_destino_id=datos['banco_destino_id'],
            divisa_id=datos['divisa_id'],
            descripcion=datos.get('descripcion', '')
        )
        db.session.add(nueva_transferencia)
        db.session.commit()
        logger.info(f"Nueva transferencia creada: {nueva_transferencia.id}")
        return jsonify({"message": "Transferencia creada exitosamente", "transferencia": nueva_transferencia.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear transferencia: {str(e)}")
        return jsonify({"error": f"Error al crear la transferencia: {str(e)}"}), 500

@banco_bp.route("/crear-conciliacion", methods=["POST"])
@login_required
def crear_conciliacion():
    datos = request.json
    logger.info(f"Datos recibidos para crear conciliación: {datos}")
    
    required_fields = ['fecha', 'banco_id', 'saldo_banco', 'saldo_libros']
    for field in required_fields:
        if not datos.get(field):
            logger.warning(f"Campo requerido faltante: {field}")
            return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400

    try:
        nueva_conciliacion = Conciliacion(
            fecha=datetime.fromisoformat(datos['fecha']),
            banco_id=datos['banco_id'],
            saldo_banco=datos['saldo_banco'],
            saldo_libros=datos['saldo_libros']
        )
        nueva_conciliacion.calcular_diferencia()
        db.session.add(nueva_conciliacion)
        db.session.commit()
        logger.info(f"Nueva conciliación creada: {nueva_conciliacion.id}")
        return jsonify({"message": "Conciliación creada exitosamente", "conciliacion": nueva_conciliacion.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al crear conciliación: {str(e)}")
        return jsonify({"error": f"Error al crear la conciliación: {str(e)}"}), 500

@banco_bp.route("/buscar-depositos")
@login_required
def buscar_depositos():
    try:
        banco_id = request.args.get('banco_id')
        fecha = request.args.get('fecha')
        monto_minimo = request.args.get('monto_minimo')

        query = Deposito.query

        if banco_id:
            query = query.filter(Deposito.banco_id == int(banco_id))
        if fecha:
            query = query.filter(Deposito.fecha == datetime.strptime(fecha, '%Y-%m-%d').date())
        if monto_minimo:
            query = query.filter(Deposito.monto >= float(monto_minimo))

        depositos = query.all()
        return jsonify([deposito.to_dict() for deposito in depositos])
    except Exception as e:
        logger.error(f"Error al buscar depósitos: {str(e)}")
        return jsonify({"error": f"Error al buscar depósitos: {str(e)}"}), 500

@banco_bp.route("/resumen-depositos")
@login_required
def resumen_depositos():
    try:
        total_depositos = db.session.query(db.func.sum(Deposito.monto)).scalar() or 0
        deposito_mas_alto = db.session.query(db.func.max(Deposito.monto)).scalar() or 0
        promedio_depositos = db.session.query(db.func.avg(Deposito.monto)).scalar() or 0

        return jsonify({
            "total_depositos": float(total_depositos),
            "deposito_mas_alto": float(deposito_mas_alto),
            "promedio_depositos": float(promedio_depositos)
        })
    except Exception as e:
        logger.error(f"Error al obtener resumen de depósitos: {str(e)}")
        return jsonify({"error": f"Error al obtener resumen de depósitos: {str(e)}"}), 500

@banco_bp.route("/grafico-depositos")
@login_required
def grafico_depositos():
    try:
        depositos_por_mes = db.session.query(
            db.func.date_trunc('month', Deposito.fecha).label('mes'),
            db.func.sum(Deposito.monto).label('total')
        ).group_by('mes').order_by('mes').all()

        return jsonify([{
            "mes": deposito.mes.strftime('%Y-%m'),
            "total": float(deposito.total)
        } for deposito in depositos_por_mes])
    except Exception as e:
        logger.error(f"Error al obtener datos para el gráfico de depósitos: {str(e)}")
        return jsonify({"error": f"Error al obtener datos para el gráfico de depósitos: {str(e)}"}), 500