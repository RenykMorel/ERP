# asistentes/banco_assistant.py
from sqlalchemy import inspect
from banco.banco_models import NuevoBanco as Banco
from models import Transaccion, Cuenta, Usuario
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from extensions import db
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

class AsistenteBancario:
    def __init__(self, db_session=None):
        """
        Inicializa el AsistenteBancario.
        
        Args:
            db_session: Sesión de SQLAlchemy (opcional, usa db.session por defecto)
        """
        self.db = db_session or db.session

    def obtener_info_bancos(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los bancos registrados.
        
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de bancos
        """
        try:
            bancos = Banco.query.all()
            return [self.object_as_dict(banco) for banco in bancos]
        except Exception as e:
            logger.error(f"Error al obtener información de bancos: {str(e)}")
            return []

    def obtener_banco_por_id(self, banco_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un banco específico por su ID.
        
        Args:
            banco_id (int): ID del banco
            
        Returns:
            Optional[Dict[str, Any]]: Diccionario con información del banco o None si no existe
        """
        try:
            banco = Banco.query.get(banco_id)
            return self.object_as_dict(banco) if banco else None
        except Exception as e:
            logger.error(f"Error al obtener banco {banco_id}: {str(e)}")
            return None

    def obtener_cuentas_banco(self, banco_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las cuentas asociadas a un banco específico.
        
        Args:
            banco_id (int): ID del banco
            
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de cuentas
        """
        try:
            cuentas = Cuenta.query.filter_by(banco_id=banco_id).all()
            return [self.object_as_dict(cuenta) for cuenta in cuentas]
        except Exception as e:
            logger.error(f"Error al obtener cuentas del banco {banco_id}: {str(e)}")
            return []

    def obtener_transacciones_cuenta(self, cuenta_id: int, 
                                   fecha_inicio: Optional[datetime] = None,
                                   fecha_fin: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las transacciones de una cuenta específica con filtro opcional por fechas.
        
        Args:
            cuenta_id (int): ID de la cuenta
            fecha_inicio (datetime, optional): Fecha de inicio para filtrar
            fecha_fin (datetime, optional): Fecha de fin para filtrar
            
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de transacciones
        """
        try:
            query = Transaccion.query.filter_by(cuenta_id=cuenta_id)
            
            if fecha_inicio:
                query = query.filter(Transaccion.fecha >= fecha_inicio)
            if fecha_fin:
                query = query.filter(Transaccion.fecha <= fecha_fin)
                
            transacciones = query.all()
            return [self.object_as_dict(transaccion) for transaccion in transacciones]
        except Exception as e:
            logger.error(f"Error al obtener transacciones de la cuenta {cuenta_id}: {str(e)}")
            return []

    def obtener_balance_cuenta(self, cuenta_id: int) -> float:
        """
        Calcula el balance actual de una cuenta específica.
        
        Args:
            cuenta_id (int): ID de la cuenta
            
        Returns:
            float: Balance actual de la cuenta
        """
        try:
            cuenta = Cuenta.query.get(cuenta_id)
            if not cuenta:
                return 0.0
            return float(cuenta.balance) if isinstance(cuenta.balance, Decimal) else cuenta.balance
        except Exception as e:
            logger.error(f"Error al obtener balance de la cuenta {cuenta_id}: {str(e)}")
            return 0.0

    def obtener_resumen_bancario(self, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene un resumen completo de la información bancaria, opcionalmente filtrado por usuario.
        
        Args:
            usuario_id (int, optional): ID del usuario para filtrar información
            
        Returns:
            Dict[str, Any]: Diccionario con resumen bancario
        """
        try:
            resumen = {
                "bancos": self.obtener_info_bancos(),
                "total_cuentas": 0,
                "balance_total": 0.0,
                "total_transacciones": 0
            }
            
            for banco in resumen["bancos"]:
                cuentas = self.obtener_cuentas_banco(banco["id"])
                if usuario_id:
                    cuentas = [c for c in cuentas if c.get("usuario_id") == usuario_id]
                
                banco["cuentas"] = cuentas
                banco["total_cuentas"] = len(cuentas)
                banco["balance_total"] = sum(float(c.get("balance", 0)) for c in cuentas)
                
                resumen["total_cuentas"] += banco["total_cuentas"]
                resumen["balance_total"] += banco["balance_total"]
                
            return resumen
        except Exception as e:
            logger.error(f"Error al obtener resumen bancario: {str(e)}")
            return {}

    def object_as_dict(self, obj) -> Dict[str, Any]:
        """
        Convierte un objeto SQLAlchemy en un diccionario.
        
        Args:
            obj: Objeto SQLAlchemy a convertir
            
        Returns:
            Dict[str, Any]: Diccionario con atributos del objeto
        """
        try:
            def serialize(value):
                if isinstance(value, datetime):
                    return value.isoformat()
                if isinstance(value, Decimal):
                    return float(value)
                return value
            
            return {c.key: serialize(getattr(obj, c.key))
                    for c in inspect(obj).mapper.column_attrs}
        except Exception as e:
            logger.error(f"Error al convertir objeto a diccionario: {str(e)}")
            return {}

    def generar_reporte_bancario(self, usuario_id: Optional[int] = None) -> List[List[Any]]:
        """
        Genera un reporte estructurado con la información bancaria.
        
        Args:
            usuario_id (int, optional): ID del usuario para filtrar información
            
        Returns:
            List[List[Any]]: Matriz con datos del reporte
        """
        try:
            resumen = self.obtener_resumen_bancario(usuario_id)
            reporte = [["Banco", "Número de Cuentas", "Balance Total", "Última Actualización"]]
            
            for banco in resumen.get("bancos", []):
                reporte.append([
                    banco["nombre"],
                    banco.get("total_cuentas", 0),
                    f"${banco.get('balance_total', 0):,.2f}",
                    banco.get("ultima_actualizacion", "N/A")
                ])
                
            return reporte
        except Exception as e:
            logger.error(f"Error al generar reporte bancario: {str(e)}")
            return [["Error al generar reporte"]]