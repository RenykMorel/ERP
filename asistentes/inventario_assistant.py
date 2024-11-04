from sqlalchemy import inspect
from inventario.inventario_models import InventarioItem, MovimientoInventario, AjusteInventario, TipoItem, CategoriaItem, Almacen
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from extensions import db
from decimal import Decimal

logger = logging.getLogger(__name__)

class AsistenteInventario:
    def __init__(self, db_session=None):
        """
        Inicializa el AsistenteInventario.
        
        Args:
            db_session: Sesión de SQLAlchemy (opcional, usa db.session por defecto)
        """
        self.db = db_session or db.session

    def obtener_items(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los items en inventario.
        
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de items
        """
        try:
            items = InventarioItem.query.all()
            return [self.object_as_dict(item) for item in items]
        except Exception as e:
            logger.error(f"Error al obtener información de items: {str(e)}")
            return []

    def obtener_item_por_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un item específico por su ID.
        
        Args:
            item_id (int): ID del item
            
        Returns:
            Optional[Dict[str, Any]]: Diccionario con información del item o None si no existe
        """
        try:
            item = InventarioItem.query.get(item_id)
            return self.object_as_dict(item) if item else None
        except Exception as e:
            logger.error(f"Error al obtener item {item_id}: {str(e)}")
            return None

    def obtener_movimientos(self, fecha_inicio: Optional[datetime] = None,
                          fecha_fin: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Obtiene los movimientos de inventario con filtro opcional por fechas.
        
        Args:
            fecha_inicio (datetime, optional): Fecha de inicio para filtrar
            fecha_fin (datetime, optional): Fecha de fin para filtrar
            
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de movimientos
        """
        try:
            query = MovimientoInventario.query
            
            if fecha_inicio:
                query = query.filter(MovimientoInventario.fecha >= fecha_inicio)
            if fecha_fin:
                query = query.filter(MovimientoInventario.fecha <= fecha_fin)
                
            movimientos = query.all()
            return [self.object_as_dict(movimiento) for movimiento in movimientos]
        except Exception as e:
            logger.error(f"Error al obtener movimientos: {str(e)}")
            return []

    def obtener_stock_actual(self, item_id: int) -> float:
        """
        Calcula el stock actual de un item específico.
        
        Args:
            item_id (int): ID del item
            
        Returns:
            float: Stock actual del item
        """
        try:
            item = InventarioItem.query.get(item_id)
            if not item:
                return 0.0
            return float(item.stock)
        except Exception as e:
            logger.error(f"Error al obtener stock del item {item_id}: {str(e)}")
            return 0.0

    def obtener_items_bajo_stock(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de items con stock por debajo del mínimo.
        
        Returns:
            List[Dict[str, Any]]: Lista de items con bajo stock
        """
        try:
            items = InventarioItem.query.filter(
                InventarioItem.stock <= InventarioItem.stock_minimo
            ).all()
            return [self.object_as_dict(item) for item in items]
        except Exception as e:
            logger.error(f"Error al obtener items con bajo stock: {str(e)}")
            return []

    def obtener_almacenes(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los almacenes.
        
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de almacenes
        """
        try:
            almacenes = Almacen.query.all()
            return [self.object_as_dict(almacen) for almacen in almacenes]
        except Exception as e:
            logger.error(f"Error al obtener almacenes: {str(e)}")
            return []

    def obtener_tipos_item(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los tipos de items registrados.
        
        Returns:
            List[Dict[str, Any]]: Lista de tipos de items
        """
        try:
            tipos = TipoItem.query.all()
            return [self.object_as_dict(tipo) for tipo in tipos]
        except Exception as e:
            logger.error(f"Error al obtener tipos de item: {str(e)}")
            return []

    def obtener_categorias(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las categorías de items.
        
        Returns:
            List[Dict[str, Any]]: Lista de categorías
        """
        try:
            categorias = CategoriaItem.query.all()
            return [self.object_as_dict(categoria) for categoria in categorias]
        except Exception as e:
            logger.error(f"Error al obtener categorías: {str(e)}")
            return []

    def obtener_resumen_inventario(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo del inventario.
        
        Returns:
            Dict[str, Any]: Diccionario con resumen del inventario
        """
        try:
            resumen = {
                "total_items": 0,
                "valor_total": 0.0,
                "items_bajo_stock": 0,
                "movimientos_recientes": [],
                "categorias": {},
                "almacenes": {}
            }
            
            # Contar items y calcular valor total
            items = self.obtener_items()
            resumen["total_items"] = len(items)
            resumen["valor_total"] = sum(float(item["costo"]) * float(item["stock"]) for item in items)
            
            # Contar items bajo stock
            items_bajo_stock = self.obtener_items_bajo_stock()
            resumen["items_bajo_stock"] = len(items_bajo_stock)
            
            # Obtener movimientos recientes (últimos 10)
            movimientos = MovimientoInventario.query.order_by(
                MovimientoInventario.fecha.desc()
            ).limit(10).all()
            resumen["movimientos_recientes"] = [self.object_as_dict(mov) for mov in movimientos]
            
            # Agrupar por categorías
            for item in items:
                categoria = item.get("categoria", "Sin categoría")
                if categoria not in resumen["categorias"]:
                    resumen["categorias"][categoria] = {
                        "total_items": 0,
                        "valor_total": 0.0
                    }
                resumen["categorias"][categoria]["total_items"] += 1
                resumen["categorias"][categoria]["valor_total"] += float(item["costo"]) * float(item["stock"])
            
            # Información de almacenes
            almacenes = self.obtener_almacenes()
            for almacen in almacenes:
                resumen["almacenes"][almacen["nombre"]] = {
                    "capacidad": almacen["capacidad"],
                    "ubicacion": almacen["ubicacion"]
                }
            
            return resumen
        except Exception as e:
            logger.error(f"Error al obtener resumen de inventario: {str(e)}")
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

    def generar_reporte_inventario(self, tipo_reporte: str = "general") -> List[List[Any]]:
        """
        Genera un reporte estructurado del inventario.
        
        Args:
            tipo_reporte (str): Tipo de reporte a generar ("general", "movimientos", "bajo_stock")
            
        Returns:
            List[List[Any]]: Matriz con datos del reporte
        """
        try:
            if tipo_reporte == "general":
                reporte = [["Item", "Código", "Categoría", "Stock", "Costo", "Valor Total"]]
                items = self.obtener_items()
                for item in items:
                    reporte.append([
                        item["nombre"],
                        item["codigo"],
                        item.get("categoria", "Sin categoría"),
                        item["stock"],
                        f"${float(item['costo']):,.2f}",
                        f"${float(item['costo']) * float(item['stock']):,.2f}"
                    ])
                
            elif tipo_reporte == "movimientos":
                reporte = [["Fecha", "Tipo", "Item", "Cantidad", "Usuario"]]
                movimientos = self.obtener_movimientos()
                for mov in movimientos:
                    item = self.obtener_item_por_id(mov["item_id"])
                    reporte.append([
                        mov["fecha"],
                        mov["tipo"],
                        item["nombre"] if item else "N/A",
                        mov["cantidad"],
                        mov.get("usuario_id", "N/A")
                    ])
                    
            elif tipo_reporte == "bajo_stock":
                reporte = [["Item", "Código", "Stock Actual", "Stock Mínimo", "Diferencia"]]
                items = self.obtener_items_bajo_stock()
                for item in items:
                    reporte.append([
                        item["nombre"],
                        item["codigo"],
                        item["stock"],
                        item["stock_minimo"],
                        item["stock_minimo"] - item["stock"]
                    ])
                    
            else:
                return [["Tipo de reporte no válido"]]
                
            return reporte
        except Exception as e:
            logger.error(f"Error al generar reporte de inventario: {str(e)}")
            return [["Error al generar reporte"]]