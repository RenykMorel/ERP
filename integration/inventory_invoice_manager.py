from flask import current_app
from extensions import db
from datetime import datetime
from facturas.facturas_models import Facturacion, NotaCredito
from inventario.inventario_models import InventarioItem
from common.models import ItemFactura, MovimientoInventario

class InventoryInvoiceManager:
    @staticmethod
    def validate_stock_for_invoice(items):
        """
        Valida que haya suficiente stock para todos los items de una factura
        
        Args:
            items (list): Lista de diccionarios con item_id y cantidad
        
        Returns:
            tuple: (bool, str) - (True si hay suficiente stock, mensaje de error si no)
        """
        for item_data in items:
            item = InventarioItem.query.get(item_data['item_id'])
            if not item:
                return False, f"Item con ID {item_data['item_id']} no encontrado"
                
            if item.tipo == 'producto':
                if item.stock < item_data['cantidad']:
                    return False, f"Stock insuficiente para {item.nombre}. Disponible: {item.stock}, Solicitado: {item_data['cantidad']}"
        
        return True, ""

    @staticmethod
    def process_invoice_creation(invoice_data, user_id):
        """
        Procesa la creación de una factura actualizando el inventario
        
        Args:
            invoice_data (dict): Datos de la factura
            user_id (int): ID del usuario que crea la factura
        
        Returns:
            tuple: (Facturacion, str) - (Objeto factura creado, mensaje de error si hay)
        """
        try:
            # Validar stock
            stock_valid, error_msg = InventoryInvoiceManager.validate_stock_for_invoice(invoice_data['items'])
            if not stock_valid:
                return None, error_msg

            # Crear factura
            nueva_factura = Facturacion(
                numero=invoice_data['numero'],
                cliente_id=invoice_data['cliente_id'],
                fecha=datetime.strptime(invoice_data['fecha'], '%Y-%m-%d'),
                total=invoice_data['total'],
                estatus='pendiente',
                usuario_id=user_id
            )
            db.session.add(nueva_factura)
            
            # Procesar items y actualizar inventario
            for item_data in invoice_data['items']:
                item = InventarioItem.query.get(item_data['item_id'])
                
                # Crear item de factura
                item_factura = ItemFactura(
                    factura=nueva_factura,
                    item=item,
                    cantidad=item_data['cantidad'],
                    precio_unitario=item_data['precio_unitario']
                )
                db.session.add(item_factura)
                
                # Actualizar stock si es producto
                if item.tipo == 'producto':
                    item.stock -= item_data['cantidad']
                    
                    # Registrar movimiento
                    movimiento = MovimientoInventario(
                        item_id=item.id,
                        tipo='salida',
                        cantidad=item_data['cantidad'],
                        fecha=datetime.utcnow(),
                        usuario_id=user_id,
                        motivo='Factura',
                        documento_referencia=nueva_factura.numero
                    )
                    db.session.add(movimiento)
            
            db.session.commit()
            return nueva_factura, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error en process_invoice_creation: {str(e)}")
            return None, f"Error al procesar la factura: {str(e)}"

    @staticmethod
    def process_invoice_cancellation(invoice_id, user_id):
        """
        Procesa la cancelación de una factura devolviendo items al inventario
        """
        try:
            factura = Facturacion.query.get(invoice_id)
            if not factura:
                return False, "Factura no encontrada"
                
            if factura.estatus == 'anulada':
                return False, "La factura ya está anulada"
            
            # Devolver items al inventario
            for item_factura in factura.items:
                if item_factura.item.tipo == 'producto':
                    item_factura.item.stock += item_factura.cantidad
                    
                    # Registrar movimiento de devolución
                    movimiento = MovimientoInventario(
                        item_id=item_factura.item_id,
                        tipo='entrada',
                        cantidad=item_factura.cantidad,
                        fecha=datetime.utcnow(),
                        usuario_id=user_id,
                        motivo='Cancelación de Factura',
                        documento_referencia=factura.numero
                    )
                    db.session.add(movimiento)
            
            factura.estatus = 'anulada'
            db.session.commit()
            return True, "Factura cancelada correctamente"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error en process_invoice_cancellation: {str(e)}")
            return False, f"Error al cancelar la factura: {str(e)}"

    @staticmethod
    def process_credit_note(credit_note_data, user_id):
        """
        Procesa una nota de crédito actualizando el inventario si es necesario
        """
        try:
            factura = Facturacion.query.get(credit_note_data['factura_id'])
            if not factura:
                return None, "Factura no encontrada"
            
            nota_credito = NotaCredito(
                numero=credit_note_data['numero'],
                factura_id=credit_note_data['factura_id'],
                monto=credit_note_data['monto'],
                fecha=datetime.strptime(credit_note_data['fecha'], '%Y-%m-%d'),
                motivo=credit_note_data['motivo'],
                usuario_id=user_id
            )
            db.session.add(nota_credito)
            
            # Si la nota de crédito implica devolución de productos
            if credit_note_data.get('devolucion_items'):
                for item_data in credit_note_data['devolucion_items']:
                    item = InventarioItem.query.get(item_data['item_id'])
                    if item.tipo == 'producto':
                        item.stock += item_data['cantidad']
                        
                        # Registrar movimiento
                        movimiento = MovimientoInventario(
                            item_id=item.id,
                            tipo='entrada',
                            cantidad=item_data['cantidad'],
                            fecha=datetime.utcnow(),
                            usuario_id=user_id,
                            motivo='Nota de Crédito',
                            documento_referencia=nota_credito.numero
                        )
                        db.session.add(movimiento)
            
            db.session.commit()
            return nota_credito, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error en process_credit_note: {str(e)}")
            return None, f"Error al procesar la nota de crédito: {str(e)}"