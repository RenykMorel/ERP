import sys
import py_avataaars as pa
import pydenticon
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from PIL import Image
from datetime import datetime
from decimal import Decimal
import json
import sqlite3
import threading
import queue
import requests
import io
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QScrollArea,
    QLineEdit,
    QStackedWidget,
    QTextEdit,
    QCalendarWidget,
    QListWidget,  # Añadido para TaskWidget y NotificationWidget
    QListWidgetItem,  # Añadido para TaskWidget y NotificationWidget
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPixmap, QImage, QBrush
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QLineSeries,
    QBarSet,
    QBarSeries,
    QBarCategoryAxis,
    QPieSeries,
    QSplineSeries,
    QValueAxis,
    QCategoryAxis,
)


class RectangularButton(QPushButton):
    def __init__(self, text, color, width=200, height=50):
        super().__init__(text)
        self.setFixedSize(width, height)
        self.color = color
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                font-weight: bold;
                border-radius: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {QColor(color).darker(110).name()};
            }}
        """
        )


class SubmoduleButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                text-align: left;
                padding: 5px 15px;
                font-size: 12px;
                border-radius: 15px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """
        )


class TaskWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("Tareas Pendientes")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.task_list = QListWidget()
        layout.addWidget(self.task_list)

        # Añadir algunas tareas de ejemplo
        self.add_task("Revisar facturas pendientes", "2023-08-15")
        self.add_task("Preparar informe mensual", "2023-08-20")
        self.add_task("Reunión con inversores", "2023-08-25")

    def add_task(self, description, due_date):
        item = QListWidgetItem(f"{description} - Vence: {due_date}")
        self.task_list.addItem(item)


class NotificationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("Notificaciones y Alertas")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.notification_list = QListWidget()
        layout.addWidget(self.notification_list)

        # Añadir algunas notificaciones de ejemplo
        self.add_notification("Nuevo cliente registrado", "info")
        self.add_notification("Factura #1234 vencida", "warning")
        self.add_notification("Actualización del sistema disponible", "info")

    def add_notification(self, message, level):
        item = QListWidgetItem(message)
        if level == "warning":
            item.setForeground(Qt.red)
        elif level == "info":
            item.setForeground(Qt.blue)
        self.notification_list.addItem(item)


class NotificationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("Notificaciones y Alertas")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.notification_list = QListWidget()
        layout.addWidget(self.notification_list)

        # Añadir algunas notificaciones de ejemplo
        self.add_notification("Nuevo cliente registrado", "info")
        self.add_notification("Factura #1234 vencida", "warning")
        self.add_notification("Actualización del sistema disponible", "info")

    def add_notification(self, message, level):
        item = QListWidgetItem(message)
        if level == "warning":
            item.setForeground(Qt.red)
        elif level == "info":
            item.setForeground(Qt.blue)
        self.notification_list.addItem(item)


class AsistenteVirtual:
    def __init__(self, erp, api_key):
        self.erp = erp
        self.api_key = api_key
        self.context = "Eres un asistente virtual para CalculAI. Debes responder preguntas basándote únicamente en la información proporcionada por el sistema y si quieren hacer calculos matemaicos ayuda."
        self.conn = sqlite3.connect("asistente_virtual.db", check_same_thread=False)
        self.crear_tablas()
        self.lock = threading.Lock()
        self.cola_actualizaciones = queue.Queue()
        threading.Thread(target=self.procesar_actualizaciones, daemon=True).start()

    def crear_tablas(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS historial (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    modulo TEXT,
                    accion TEXT,
                    datos TEXT
                )
            """
            )

    def entrenar(self, modulo, accion, datos):
        self.cola_actualizaciones.put((modulo, accion, datos))

    def procesar_actualizaciones(self):
        while True:
            modulo, accion, datos = self.cola_actualizaciones.get()
            with self.lock:
                with self.conn:
                    self.conn.execute(
                        """
                        INSERT INTO historial (timestamp, modulo, accion, datos)
                        VALUES (?, ?, ?, ?)
                    """,
                        (datetime.now().isoformat(), modulo, accion, json.dumps(datos)),
                    )
            self.cola_actualizaciones.task_done()

    def _obtener_contexto_relevante(self, n=5):
        with self.lock:
            with self.conn:
                cursor = self.conn.execute(
                    "SELECT * FROM historial ORDER BY timestamp DESC LIMIT ?", (n,)
                )
                historial = cursor.fetchall()
            contexto_relevante = [json.dumps(dict(row)) for row in historial]
            return "\n".join(contexto_relevante)

    def responder(self, pregunta):
        contexto_relevante = self._obtener_contexto_relevante()
        prompt = f"{self.context}\n\nContexto relevante:\n{contexto_relevante}\n\nHuman: {pregunta}\n\nAssistant:"

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        data = {
            "model": "claude-2.1",
            "prompt": prompt,
            "max_tokens_to_sample": 300,
            "temperature": 0.7,
            "stop_sequences": ["\n\nHuman:"],
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/complete",
                headers=headers,
                json=data,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()["completion"].strip()
        except requests.exceptions.RequestException as e:
            if response.status_code == 401:
                return "Error de autenticación. Por favor, verifica tu clave API."
            elif response.status_code == 429:
                return "Se ha excedido el límite de solicitudes. Intenta de nuevo más tarde."
            else:
                return f"Error al obtener respuesta: {str(e)}"
        except (KeyError, json.JSONDecodeError):
            return "Error al procesar la respuesta del servidor."
        except Exception as e:
            return f"Error inesperado: {str(e)}"

    def analizar_estadisticas(self, tipo_analisis):
        datos_relevantes = self.erp.obtener_datos_para_analisis(tipo_analisis)
        prompt = f"Realiza un análisis estadístico avanzado de tipo {tipo_analisis} con los siguientes datos:\n{json.dumps(datos_relevantes)}\n\nAnálisis:"

        return self.responder(prompt)

    def proyectar_tendencias(self, anos):
        datos_historicos = self.erp.obtener_datos_historicos()
        prompt = f"Basándote en los siguientes datos históricos, proyecta las tendencias para los próximos {anos} años:\n{json.dumps(datos_historicos)}\n\nProyección:"

        return self.responder(prompt)


class ModuloBanco(QWidget):
    def __init__(self, erp_main):
        super().__init__()
        self.erp_main = erp_main
        self.init_ui()
        self.transacciones = []
        self.ia_model = self.entrenar_modelo_ia()

    def init_ui(self):
        layout = QVBoxLayout()

        # Título del módulo
        titulo = QLabel("Banco")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(titulo)

        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Barra de navegación ajustada
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(1)  # Reduce el espacio entre botones
        nav_buttons = ["Buscar Banco", "Banco", "Buscar Cuenta Banco", "Cuenta Banco"]
        for i, button_text in enumerate(nav_buttons):
            button = QPushButton(button_text)
            button.setStyleSheet(
                """
                QPushButton {
                    color: blue;
                    background-color: transparent;
                    border: none;
                    padding: 5px;
                    text-align: left;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """
            )
            nav_bar.addWidget(button)
            if (
                i < len(nav_buttons) - 1
            ):  # Añade separador excepto después del último botón
                separator = QLabel("|")
                separator.setStyleSheet("color: gray;")
                nav_bar.addWidget(separator)
        nav_bar.addStretch(1)  # Empuja los botones hacia la izquierda
        layout.addLayout(nav_bar)

        # Otra línea separadora
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        # Formulario de búsqueda
        form_layout = QFormLayout()
        self.id_input = QLineEdit()
        self.id_input.setFixedWidth(150)  # Ajustado a un ancho más pequeño
        self.nombre_input = QLineEdit()
        self.nombre_input.setFixedWidth(250)  # Ajustado a un ancho más pequeño
        self.contacto_input = QLineEdit()
        self.contacto_input.setFixedWidth(250)  # Ajustado a un ancho más pequeño
        self.estatus_combo = QComboBox()
        self.estatus_combo.addItems(["Todos", "Activo", "Inactivo"])
        self.estatus_combo.setFixedWidth(150)  # Ajustado a un ancho más pequeño

        form_layout.addRow("ID:", self.id_input)
        form_layout.addRow("Nombre:", self.nombre_input)
        form_layout.addRow("Contacto:", self.contacto_input)
        form_layout.addRow("Estatus:", self.estatus_combo)

        layout.addLayout(form_layout)

        # Línea separadora antes de los botones
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line3)

        # Botones de acción
        button_layout = QHBoxLayout()
        self.buscar_btn = QPushButton("Buscar")
        self.buscar_btn.setStyleSheet(
            "background-color: orange; color: white; padding: 5px 15px;"
        )
        self.crear_btn = QPushButton("Crear Nuevo")
        self.crear_btn.setStyleSheet(
            "background-color: orange; color: white; padding: 5px 15px;"
        )
        button_layout.addWidget(self.buscar_btn)
        button_layout.addWidget(self.crear_btn)
        button_layout.addStretch()  # Esto empujará los botones hacia la izquierda
        layout.addLayout(button_layout)

        # Etiqueta "Resultado de Búsqueda"
        resultado_label = QLabel("Resultado de Búsqueda")
        resultado_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(resultado_label)

        # Tabla de resultados
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nombre",
                "Teléfono",
                "Contacto",
                "Teléfono Contacto",
                "Estatus",
                "Acción",
            ]
        )
        layout.addWidget(self.results_table)

        # Conectar botones a funciones
        self.buscar_btn.clicked.connect(self.buscar_bancos)
        self.crear_btn.clicked.connect(self.crear_nuevo_banco)

        self.setLayout(layout)

    def buscar_bancos(self):
        # Implementación de ejemplo
        self.results_table.setRowCount(3)
        sample_data = [
            (
                "1",
                "BANCO MÚLTIPLE CARIBE INTERNACIONAL S.A",
                "809380000",
                "",
                "",
                "Activo",
                "",
            ),
            ("2", "BANCO MÚLTIPLE SANTA CRUZ S.A", "809555777", "", "", "Activo", ""),
            ("3", "THE BANK OF NOVA SCOTIA", "809820000", "", "", "Activo", ""),
        ]
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                self.results_table.setItem(row, col, QTableWidgetItem(value))
            edit_btn = QPushButton("Editar")
            self.results_table.setCellWidget(row, 6, edit_btn)

    def crear_nuevo_banco(self):
        print("Crear nuevo banco")

    # ... (otros métodos si son necesarios)

    def entrenar_modelo_ia(self):
        # Simulación de entrenamiento de modelo de IA para detección de anomalías
        X = np.random.rand(100, 2)  # Datos de ejemplo
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = KMeans(n_clusters=3)
        model.fit(X_scaled)
        return model, scaler

    def es_transaccion_inusual(self, monto):
        model, scaler = self.ia_model
        # Convertir el monto a un array 2D para el escalador
        monto_scaled = scaler.transform([[monto, 0]])  # El 0 es un placeholder
        cluster = model.predict(monto_scaled)
        # Suponemos que el cluster 2 representa transacciones inusuales
        return cluster[0] == 2

    # Añadir aquí los métodos buscar_bancos, crear_nuevo_banco, exportar_a_excel,
    # y otros métodos necesarios como en el ejemplo anterior

    def buscar_bancos(self):
        # Implementación de ejemplo
        self.results_table.setRowCount(3)
        sample_data = [
            (
                "1",
                "BANCO MÚLTIPLE CARIBE INTERNACIONAL S.A",
                "809380000",
                "",
                "",
                "Activo",
                "",
            ),
            ("2", "BANCO MÚLTIPLE SANTA CRUZ S.A", "809555777", "", "", "Activo", ""),
            ("3", "THE BANK OF NOVA SCOTIA", "809820000", "", "", "Activo", ""),
        ]
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                self.results_table.setItem(row, col, QTableWidgetItem(value))
            edit_btn = QPushButton("Editar")
            self.results_table.setCellWidget(row, 6, edit_btn)

    def crear_nuevo_banco(self):
        print("Crear nuevo banco")

    def exportar_a_excel(self):
        print("Exportar a Excel")

    def inicializar_paginas_submodulos(self):
        self.pagina_depositos = self.crear_pagina_depositos()
        self.pagina_notas = self.crear_pagina_notas()
        self.pagina_transferencias = self.crear_pagina_transferencias()
        self.pagina_conciliacion = self.crear_pagina_conciliacion()
        self.pagina_gestion = self.crear_pagina_gestion()

        self.contenido_principal.addWidget(self.pagina_depositos)
        self.contenido_principal.addWidget(self.pagina_notas)
        self.contenido_principal.addWidget(self.pagina_transferencias)
        self.contenido_principal.addWidget(self.pagina_conciliacion)
        self.contenido_principal.addWidget(self.pagina_gestion)

    def mostrar_submodulo(self, submodulo):
        if submodulo == "depositos":
            self.contenido_principal.setCurrentWidget(self.pagina_depositos)
        elif submodulo == "notas":
            self.contenido_principal.setCurrentWidget(self.pagina_notas)
        elif submodulo == "transferencias":
            self.contenido_principal.setCurrentWidget(self.pagina_transferencias)
        elif submodulo == "conciliacion":
            self.contenido_principal.setCurrentWidget(self.pagina_conciliacion)
        elif submodulo == "gestion":
            self.contenido_principal.setCurrentWidget(self.pagina_gestion)

    def crear_pagina_depositos(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # Formulario de depósito
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Monto:"))
        self.input_monto = QLineEdit()
        form_layout.addWidget(self.input_monto)
        form_layout.addWidget(QLabel("Cuenta:"))
        self.combo_cuenta = QComboBox()
        self.combo_cuenta.addItems(["Cuenta 1", "Cuenta 2", "Cuenta 3"])  # Ejemplo
        form_layout.addWidget(self.combo_cuenta)
        btn_depositar = QPushButton("Realizar Depósito")
        btn_depositar.clicked.connect(self.realizar_deposito)
        form_layout.addWidget(btn_depositar)

        layout.addLayout(form_layout)

        # Tabla de depósitos
        self.tabla_depositos = QTableWidget(0, 3)
        self.tabla_depositos.setHorizontalHeaderLabels(["Fecha", "Monto", "Cuenta"])
        layout.addWidget(self.tabla_depositos)

        return page

    def crear_pagina_notas(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Aquí irá el contenido para Notas de Crédito/Débito"))
        return page

    def crear_pagina_transferencias(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Aquí irá el contenido para Transferencias"))
        return page

    def crear_pagina_conciliacion(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Aquí irá el contenido para Conciliación Bancaria"))
        return page

    def crear_pagina_gestion(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Aquí irá el contenido para Gestión de Bancos"))
        return page


class ERP(QMainWindow):
    def __init__(self, claude_api_key):
        super().__init__()
        self.asistente = AsistenteVirtual(self, claude_api_key)
        self.modulos = {}  # Diccionario para almacenar los módulos
        self.init_ui()
        self.inicializar_modulos()

    def inicializar_modulos(self):
        self.modulos = {}
        self.modulos["banco"] = ModuloBanco(self)
        self.content_area_widget.addWidget(self.modulos["banco"])

    def on_menu_item_clicked(self, menu_item_name):
        if menu_item_name in self.modulos:
            self.content_area_widget.setCurrentWidget(self.modulos[menu_item_name])
        else:
            print(f"Módulo {menu_item_name} no implementado")

    def init_ui(self):
        self.setWindowTitle("CalculAI")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(
            """
            QMainWindow {background-color: #f0f0f0;}
            QLabel {font-size: 14px;}
        """
        )

        main_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.header(main_layout)
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        self.sidebar(content_layout)
        self.content_area(content_layout)
        self.assistant_column(content_layout)

    def generate_avatar(self, seed):
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Usar el seed para generar un color
        color = QColor(hash(seed) % 256, hash(seed * 2) % 256, hash(seed * 3) % 256)

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 100, 100)

        painter.end()
        return pixmap

    def user_info(self, sidebar_layout):
        user_info_widget = QWidget()
        user_info_layout = QVBoxLayout(user_info_widget)

        user_photo = QLabel()

        # Asume que tienes una función get_current_user() que devuelve la información del usuario actual
        current_user = self.get_current_user()

        if current_user and current_user.photo_path:
            pixmap = QPixmap(current_user.photo_path)
        else:
            # Genera un avatar usando el ID del usuario como seed
            user_id = current_user.id if current_user else "default"
            pixmap = self.generate_avatar(user_id)

        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            user_photo.setPixmap(scaled_pixmap)
            user_photo.setStyleSheet("border-radius: 50px; border: 2px solid white;")
            user_photo.setFixedSize(100, 100)
            user_photo.setScaledContents(True)
        else:
            user_photo.setText("No image")
            user_photo.setStyleSheet("color: white; font-size: 12px;")

        user_info_layout.addWidget(user_photo, alignment=Qt.AlignCenter)

        user_name = QLabel(current_user.name if current_user else "Usuario")
        user_name.setStyleSheet("font-weight: bold; font-size: 16px; color: white;")
        user_info_layout.addWidget(user_name, alignment=Qt.AlignCenter)

        user_id = QLabel(current_user.id if current_user else "")
        user_id.setStyleSheet("font-size: 14px; color: #CCCCCC;")
        user_info_layout.addWidget(user_id, alignment=Qt.AlignCenter)

        sidebar_layout.addWidget(user_info_widget)

    def get_current_user(self):
        class User:
            def __init__(self):
                self.id = "P11863"
                self.name = "Renyk Morel"
                self.photo_path = (
                    None  # Mantenemos esto como None para que se genere un avatar
                )

        return User()

    def header(self, main_layout):
        header = QLabel("CalculAI")
        header.setFont(QFont("Arial", 32, QFont.Bold))
        header.setStyleSheet("margin-bottom: 20px; color: #00A8E8; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

    def sidebar(self, content_layout):
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #007EA7; color: white;")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)

        self.user_info(sidebar_layout)
        self.create_menu_items(sidebar_layout)

        content_layout.addWidget(sidebar)

    def create_menu_items(
        self, sidebar_layout
    ):  # AQUI SE AGREGAN LOS NOMBRES Y COLOR DE LOS ITEM
        colors = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#FFA07A",
            "#FFC0CB",
            "#98D8C8",
            "#F06292",
            "#AED581",
            "#FFD54F",
            "#800000",
            "#4DB6AC",
            "#075e56",
        ]

        menu_items = [
            "banco",
            "contabilidad",
            "activos_fijos",
            "cuentas_por_cobrar",
            "cuentas_por_pagar",
            "facturacion",
            "impuestos",
            "inventario",
            "compras",
            "Importacion",
            "proyectos",
            "recursos_humanos",
        ]

        for i, item_name in enumerate(menu_items):
            btn = RectangularButton(
                item_name.replace("_", " ").title(), colors[i % len(colors)]
            )
            btn.clicked.connect(
                lambda checked, name=item_name: self.on_menu_item_clicked(name)
            )
            sidebar_layout.addWidget(btn, alignment=Qt.AlignCenter)

            # Crear submódulos
            submodules = getattr(self, f"{item_name}_submodules")()
            for submodule in submodules:
                submodule_btn = SubmoduleButton(submodule)
                submodule_btn.hide()
                submodule_btn.clicked.connect(
                    lambda checked, text=submodule: self.on_submodule_clicked(text)
                )
                sidebar_layout.addWidget(submodule_btn, alignment=Qt.AlignCenter)

                setattr(
                    self,
                    f"submodule_{item_name}_{submodule.lower().replace(' ', '_').replace('/', '_')}",
                    submodule_btn,
                )

        sidebar_layout.addStretch()

    def on_menu_item_clicked(self, menu_item_name):
        if menu_item_name in self.modulos:
            self.content_area_widget.setCurrentWidget(self.modulos[menu_item_name])
        else:
            print(f"Módulo {menu_item_name} no implementado")

        # Mantener el código existente para manejar submódulos
        submodules = getattr(self, f"{menu_item_name}_submodules")()
        first_submodule = getattr(
            self,
            f"submodule_{menu_item_name}_{submodules[0].lower().replace(' ', '_').replace('/', '_')}",
        )
        are_submodules_visible = first_submodule.isVisible()

        if are_submodules_visible:
            for submodule in submodules:
                submodule_btn = getattr(
                    self,
                    f"submodule_{menu_item_name}_{submodule.lower().replace(' ', '_').replace('/', '_')}",
                )
                submodule_btn.hide()
        else:
            for widget in self.findChildren(SubmoduleButton):
                widget.hide()

            for submodule in submodules:
                submodule_btn = getattr(
                    self,
                    f"submodule_{menu_item_name}_{submodule.lower().replace(' ', '_').replace('/', '_')}",
                )
                submodule_btn.show()

    def on_submodule_clicked(self, submodule_name):
        print(f"Clicked on {submodule_name}")
        # Aquí puedes añadir la lógica para manejar el clic en el submódulo

    def content_area(self, content_layout):
        self.content_area_widget = QStackedWidget()
        self.home_page()
        self.submodules_widget()
        content_layout.addWidget(self.content_area_widget, 1)

    def home_page(self):
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)

        # Fila superior para KPIs y controles de gráficos
        top_layout = QHBoxLayout()

        # Botones de control para los gráficos
        line_chart_btn = QPushButton("Mostrar/Ocultar Gráfico de Líneas")
        bar_chart_btn = QPushButton("Mostrar/Ocultar Gráfico de Barras")
        pie_chart_btn = QPushButton("Mostrar/Ocultar Gráfico Circular")

        top_layout.addWidget(line_chart_btn)
        top_layout.addWidget(bar_chart_btn)
        top_layout.addWidget(pie_chart_btn)

        home_layout.addLayout(top_layout)

        # Fila media para gráficos y calendario
        charts_calendar_layout = QHBoxLayout()

        self.charts_layout = QVBoxLayout()
        self.line_chart_widget = self.line_chart()
        self.bar_chart_widget = self.bar_chart()
        self.pie_chart_widget = self.pie_chart()

        self.charts_layout.addWidget(self.line_chart_widget)
        self.charts_layout.addWidget(self.bar_chart_widget)
        self.charts_layout.addWidget(self.pie_chart_widget)

        charts_calendar_layout.addLayout(self.charts_layout)

        calendar_widget = QCalendarWidget()
        calendar_widget.setFixedWidth(300)
        charts_calendar_layout.addWidget(calendar_widget)

        home_layout.addLayout(charts_calendar_layout)

        # Fila inferior para tareas y notificaciones
        bottom_layout = QHBoxLayout()

        task_widget = TaskWidget()
        bottom_layout.addWidget(task_widget)

        notification_widget = NotificationWidget()
        bottom_layout.addWidget(notification_widget)

        home_layout.addLayout(bottom_layout)

        # Conectar los botones a las funciones de mostrar/ocultar
        line_chart_btn.clicked.connect(
            lambda: self.toggle_chart_visibility(self.line_chart_widget)
        )
        bar_chart_btn.clicked.connect(
            lambda: self.toggle_chart_visibility(self.bar_chart_widget)
        )
        pie_chart_btn.clicked.connect(
            lambda: self.toggle_chart_visibility(self.pie_chart_widget)
        )

        self.content_area_widget.addWidget(home_page)

    def toggle_chart_visibility(self, chart_widget):
        if chart_widget.isVisible():
            chart_widget.hide()
        else:
            chart_widget.show()

    def line_chart(self):
        line_series = QSplineSeries()
        for i in range(6):
            line_series.append(i, 0)

        line_chart = QChart()
        line_chart.addSeries(line_series)
        line_chart.setTitle("Ventas Mensuales")

        axisX = QCategoryAxis()
        axisX.setTitleText("Meses")
        axisX.setLabelsAngle(-45)
        categories = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
        for i, category in enumerate(categories):
            axisX.append(category, i)

        axisY = QValueAxis()
        axisY.setTitleText("Ventas ($)")
        axisY.setRange(0, 100)  # Ajusta este rango según tus necesidades

        line_chart.setAxisX(axisX, line_series)
        line_chart.setAxisY(axisY, line_series)

        line_chart_view = QChartView(line_chart)
        line_chart_view.setRenderHint(QPainter.Antialiasing)
        return line_chart_view

    def bar_chart(self):
        set0 = QBarSet("Ingresos")
        set1 = QBarSet("Gastos")
        set0.append([0, 0, 0, 0, 0, 0])
        set1.append([0, 0, 0, 0, 0, 0])

        series = QBarSeries()
        series.append(set0)
        series.append(set1)

        bar_chart = QChart()
        bar_chart.addSeries(series)
        bar_chart.setTitle("Ingresos vs Gastos")

        categories = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
        axisX = QBarCategoryAxis()
        axisX.append(categories)
        axisX.setTitleText("Meses")

        axisY = QValueAxis()
        axisY.setTitleText("Monto ($)")
        axisY.setRange(0, 100)  # Ajusta este rango según tus necesidades

        bar_chart.setAxisX(axisX, series)
        bar_chart.setAxisY(axisY, series)

        bar_chart_view = QChartView(bar_chart)
        bar_chart_view.setRenderHint(QPainter.Antialiasing)
        return bar_chart_view

    def pie_chart(self):
        pie_series = QPieSeries()
        pie_series.append("Ventas", 0)
        pie_series.append("Gastos", 0)
        pie_series.append("Beneficios", 0)

        pie_chart = QChart()
        pie_chart.addSeries(pie_series)
        pie_chart.setTitle("Distribución Financiera")

        pie_chart_view = QChartView(pie_chart)
        pie_chart_view.setRenderHint(QPainter.Antialiasing)
        return pie_chart_view

    def submodules_widget(self):
        self.submodules_widget = QWidget()
        self.submodules_layout = QVBoxLayout(self.submodules_widget)
        self.submodules_layout.setAlignment(Qt.AlignTop)
        self.content_area_widget.addWidget(self.submodules_widget)

    def assistant_column(self, content_layout):
        assistant_column = QWidget()
        assistant_column.setFixedWidth(300)
        assistant_column.setStyleSheet("background-color: #007EA7; color: white;")
        assistant_layout = QVBoxLayout(assistant_column)
        assistant_layout.setAlignment(Qt.AlignTop)

        assistant_title = QLabel("Asistente Virtual")
        assistant_title.setFont(QFont("Arial", 18, QFont.Bold))
        assistant_title.setStyleSheet("padding: 10px;")
        assistant_layout.addWidget(assistant_title)

        self.assistant_chat = QTextEdit()
        self.assistant_chat.setReadOnly(True)
        self.assistant_chat.setStyleSheet(
            """
            QTextEdit {
                background-color: #ecf0f1;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
        """
        )
        assistant_layout.addWidget(self.assistant_chat)

        self.assistant_input = QLineEdit()
        self.assistant_input.setPlaceholderText("Haga una pregunta...")
        self.assistant_input.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                border: 2px solid #00A8E8;
                border-radius: 20px;
                font-size: 14px;
            }
        """
        )
        self.assistant_input.returnPressed.connect(self.handle_assistant_input)
        assistant_layout.addWidget(self.assistant_input)

        content_layout.addWidget(assistant_column)

    def assistant_column(self, content_layout):
        assistant_column = QWidget()
        assistant_column.setFixedWidth(300)
        assistant_column.setStyleSheet("background-color: #007EA7; color: white;")
        assistant_layout = QVBoxLayout(assistant_column)

        assistant_title = QLabel("Asistente Virtual")
        assistant_title.setFont(QFont("Arial", 18, QFont.Bold))
        assistant_title.setStyleSheet("padding: 10px;")
        assistant_layout.addWidget(assistant_title)

        self.assistant_chat = QTextEdit()
        self.assistant_chat.setReadOnly(True)
        self.assistant_chat.setStyleSheet(
            """
            QTextEdit {
                background-color: #ecf0f1;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
        """
        )
        assistant_layout.addWidget(self.assistant_chat)

        self.assistant_input = QLineEdit()
        self.assistant_input.setPlaceholderText("Haga una pregunta...")
        self.assistant_input.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
                border: 2px solid #00A8E8;
                border-radius: 20px;
                font-size: 14px;
            }
        """
        )
        self.assistant_input.returnPressed.connect(self.handle_assistant_input)
        assistant_layout.addWidget(self.assistant_input)

        content_layout.addWidget(assistant_column)

    def handle_assistant_input(self):
        text = self.assistant_input.text().strip().lower()
        if text in ["hola", "buenos días", "buenas tardes", "buenas noches", "saludos"]:
            response = "Hola contador, soy tu Asistente Contable CalculAI, ¿qué quieres consultar?"
        else:
            self.assistant_chat.append(
                f"<span style='color: #00A8E8; font-size: 18px;'><b>Usuario:</b> {text}</span>"
            )
            self.assistant_chat.append(
                "<span style='color: #007EA7; font-size: 18px;'><b>Asistente:</b> Procesando...</span>"
            )
            QApplication.processEvents()  # Actualiza la interfaz de usuario

            response = self.asistente.responder(text)

            # Elimina el mensaje "Procesando..."
            cursor = self.assistant_chat.textCursor()
            cursor.movePosition(cursor.End)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Elimina la línea en blanco extra

        self.assistant_chat.append(
            f"<span style='color: #007EA7; font-size: 18px;'><b>Asistente:</b> {response}</span>"
        )
        self.assistant_input.clear()

    # Funciones de módulos y submódulos
    def banco(self):
        print("Módulo de Banco")

    def banco_submodules(self):
        return [
            "Depósitos",
            "Notas de Crédito/Débito",
            "Transferencias Bancarias",
            "Conciliación Bancaria",
            "Gestión de bancos",
        ]

    def contabilidad(self):
        print("Módulo de Contabilidad")

    def contabilidad_submodules(self):
        return [
            "Cuentas",
            "Diario",
            "Mayor General",
            "Balanza de Comprobación",
            "Estado de Resultados",
            "Balance General",
            "Configuraciones",
            "Flujo de caja",
        ]

    def activos_fijos(self):
        print("Módulo de Activos Fijos")

    def activos_fijos_submodules(self):
        return [
            "Activo Fijo",
            "Depreciación",
            "Retiro",
            "Revalorización",
            "Tipo de Activo Fijo",
        ]

    def cuentas_por_cobrar(self):
        print("Módulo de Cuentas por cobrar")

    def cuentas_por_cobrar_submodules(self):
        return [
            "Cliente",
            "Descuento y devoluciones",
            "Nota de credito",
            "Nota de debito",
            "Recibo",
            "Anticipo CxC",
            "Condicion de pago",
            "Reporte CxC",
            "Tipo de cliente",
        ]

    def cuentas_por_pagar(self):
        print("Módulo de Cuentas por pagar")

    def cuentas_por_pagar_submodules(self):
        return [
            "Factura Suplidor",
            "Nota de Crédito",
            "Nota de Débito",
            "Orden de Compras",
            "Suplidor",
            "Anticipo CxP",
            "Pago de Contado",
            "Reporte CxP",
            "Requisición Cotización",
            "Solicitud Compras",
            "Tipo de Suplidor",
        ]

    def facturacion(self):
        print("Módulo de Facturación")

    def facturacion_submodules(self):
        return [
            "Facturas",
            "Pre-facturas",
            "Notas de Crédito/Débito",
            "Reporte de Ventas",
            "Gestión de clientes",
        ]

    def impuestos(self):
        print("Módulo de Impuestos")

    def impuestos_submodules(self):
        return [
            "Formulario 606",
            "Formulario 607",
            "Reporte IT1",
            "Impuesto sobre la Renta (IR17)",
            "Serie Fiscal",
            "Configuraciones",
        ]

    def inventario(self):
        print("Módulo de Inventario")

    def inventario_submodules(self):
        return [
            "Items",
            "Entrada de Almacén",
            "Salida de Almacén",
            "Inventario",
            "Reporte de Inventario",
        ]

    def compras(self):
        print("Módulo de Compras")

    def compras_submodules(self):
        return [
            "Solicitudes de Compra",
            "Órdenes de Compra",
            "Recepción de Materiales",
            "Gastos",
            "Reporte de Compras/Gastos",
        ]

    def Importacion(self):
        print("Módulo de Importacion")

    def Importacion_submodules(self):
        return ["Expediente de Importacion", "Importador", "Reportes Importacion"]

    def proyectos(self):
        print("Módulo de Proyectos")

    def proyectos_submodules(self):
        return ["Gestión de Proyectos", "Presupuestos", "Facturación por Proyecto"]

    def recursos_humanos(self):
        print("Módulo de Recursos Humanos")

    def recursos_humanos_submodules(self):
        return ["Gestión de Empleados", "Nómina", "Evaluación de Desempeño"]

    def obtener_datos_para_analisis(self, tipo_analisis):
        return {
            "ventas": [100, 200, 150],
            "costos": [50, 80, 60],
            "beneficios": [50, 120, 90],
        }

    def obtener_datos_historicos(self):
        return {
            "2021": {"ventas": 1000, "costos": 700},
            "2022": {"ventas": 1200, "costos": 800},
        }

    def actualizar_grafico_lineas(self, datos):
        # Implementar la actualización del gráfico de líneas
        # Por ejemplo:
        self.line_chart_widget.chart().removeAllSeries()
        series = QSplineSeries()
        for i, valor in enumerate(datos):
            series.append(i, valor)
        self.line_chart_widget.chart().addSeries(series)
        self.line_chart_widget.chart().createDefaultAxes()

    def actualizar_grafico_barras(self, ingresos, egresos):
        # Implementar la actualización del gráfico de barras
        # Por ejemplo:
        set0 = QBarSet("Ingresos")
        set1 = QBarSet("Egresos")
        set0.append(ingresos)
        set1.append(egresos)
        series = QBarSeries()
        series.append(set0)
        series.append(set1)
        self.bar_chart_widget.chart().removeAllSeries()
        self.bar_chart_widget.chart().addSeries(series)
        self.bar_chart_widget.chart().createDefaultAxes()

    def actualizar_grafico_circular(self, distribucion):
        # Implementar la actualización del gráfico circular
        # Por ejemplo:
        series = QPieSeries()
        for key, value in distribucion.items():
            series.append(key, value)
        self.pie_chart_widget.chart().removeAllSeries()
        self.pie_chart_widget.chart().addSeries(series)

    def agregar_notificacion(self, mensaje):
        # Implementar la adición de notificaciones
        # Por ejemplo:
        self.notification_widget.add_notification(mensaje, "info")


if __name__ == "__main__":
    claude_api_key = "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"
    app = QApplication(sys.argv)
    erp_app = ERP(claude_api_key)
    erp_app.show()
    sys.exit(app.exec_())
