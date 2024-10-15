class AsistenteVirtual {
    constructor() {
        this.elements = {
            virtualAssistant: document.getElementById('virtual-assistant'),
            assistantIcon: document.getElementById('assistant-icon'),
            chatWindow: document.getElementById('chat-window'),
            minimizeChat: document.getElementById('minimize-chat'),
            chatMessages: document.getElementById('chat-messages'),
            asistenteInput: document.getElementById('assistant-input'),
            asistenteEnviar: document.getElementById('assistant-send')
        };

        this.conversationHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
        this.asistenteActivo = false;

        this.initialize();
    }

    initialize() {
        this.checkAsistenteStatus();
        this.cargarHistorialConversacion();
        this.setupEventListeners();
    }

    async checkAsistenteStatus() {
        try {
            const response = await fetch('/api/asistente_status');
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            const data = await response.json();
            console.log('Estado del asistente:', data);
            this.asistenteActivo = data.activo;
            if (this.asistenteActivo && this.conversationHistory.length === 0) {
                const mensajeBienvenida = "¡Hola! Soy tu asistente virtual de CalculAI. ¿En qué puedo ayudarte hoy?";
                this.addMessageToHistory('Asistente', mensajeBienvenida);
            }
            this.cargarHistorialConversacion();
        } catch (error) {
            console.error('Error al verificar el estado del asistente:', error);
            this.elements.chatWindow.classList.add('asistente-inactivo');
            this.mostrarMensajeAsistente("Error al verificar el estado del asistente. Por favor, intente más tarde.");
        }
    }

    cargarHistorialConversacion() {
        this.elements.chatMessages.innerHTML = '';
        this.conversationHistory.forEach(entry => {
            this.addMessageToChat(entry.sender, entry.message, entry.sender === 'Usuario' ? 'user-message' : 'assistant-message');
        });
    }

    setupEventListeners() {
        if (this.elements.virtualAssistant) {
            this.elements.virtualAssistant.addEventListener('click', () => this.openChat());
        }

        if (this.elements.minimizeChat) {
            this.elements.minimizeChat.addEventListener('click', () => this.closeChat());
        }

        if (this.elements.asistenteInput && this.elements.asistenteEnviar) {
            this.elements.asistenteEnviar.addEventListener('click', () => this.enviarMensaje());
            this.elements.asistenteInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.enviarMensaje();
                }
            });
        }

        // Verificar que todos los elementos necesarios existen
        Object.entries(this.elements).forEach(([key, element]) => {
            if (!element) {
                console.error(`El elemento ${key} no se encontró en el DOM`);
            }
        });
    }

    openChat() {
        document.body.classList.add('chat-open');
        if (this.elements.chatWindow) {
            this.elements.chatWindow.style.display = 'block';
            this.elements.asistenteInput?.focus();
        }
    }

    closeChat() {
        document.body.classList.remove('chat-open');
        if (this.elements.chatWindow) {
            this.elements.chatWindow.style.display = 'none';
        }
    }

    enviarMensaje() {
        const pregunta = this.elements.asistenteInput.value.trim();
        if (pregunta) {
            this.mostrarMensajeUsuario(pregunta);
            if (this.asistenteActivo) {
                this.notificarAsistente(pregunta);
            } else {
                this.mostrarMensajeAsistente("El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.");
            }
            this.elements.asistenteInput.value = '';
        }
    }

    mostrarMensajeUsuario(mensaje) {
        this.addMessageToChat('Usuario', mensaje, 'user-message');
    }

    mostrarMensajeAsistente(mensaje) {
        this.addMessageToChat('Asistente', mensaje, 'assistant-message');
    }

    addMessageToChat(sender, message, className) {
        const nuevoMensaje = document.createElement('p');
        nuevoMensaje.textContent = `${sender}: ${message}`;
        nuevoMensaje.className = className;
        this.elements.chatMessages.appendChild(nuevoMensaje);
        this.scrollToBottom();

        this.addMessageToHistory(sender, message);
    }

    addMessageToHistory(sender, message) {
        this.conversationHistory.push({ sender, message });
        this.guardarHistorialConversacion();
    }

    guardarHistorialConversacion() {
        localStorage.setItem('chatHistory', JSON.stringify(this.conversationHistory));
    }

    async notificarAsistente(mensaje) {
        const paginaActual = window.location.pathname;
        
        this.mostrarIndicadorCarga(true);
        
        try {
            const response = await fetch('/api/asistente', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    pregunta: mensaje,
                    pagina_actual: paginaActual
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            this.mostrarIndicadorCarga(false);

            switch (data.tipo) {
                case 'reporte':
                    this.mostrarVentanaReporte(data.datos, data.tipo_reporte);
                    this.mostrarMensajeAsistente(data.mensaje);
                    break;
                case 'texto':
                    this.mostrarMensajeAsistente(data.respuesta);
                    break;
                default:
                    console.error('Respuesta inesperada del asistente:', data);
                    this.mostrarMensajeAsistente("Lo siento, ocurrió un error al procesar tu solicitud.");
            }
        } catch (error) {
            this.mostrarIndicadorCarga(false);
            console.error('Error:', error);
            this.mostrarMensajeAsistente("Ocurrió un error al comunicarse con el asistente. Por favor, intenta de nuevo más tarde.");
        }
    }

    mostrarIndicadorCarga(mostrar) {
        const indicadorId = 'indicador-carga';
        let indicadorCarga = document.getElementById(indicadorId);

        if (mostrar && !indicadorCarga) {
            indicadorCarga = document.createElement('div');
            indicadorCarga.id = indicadorId;
            indicadorCarga.textContent = 'Cargando...';
            this.elements.chatMessages.appendChild(indicadorCarga);
        } else if (!mostrar && indicadorCarga) {
            indicadorCarga.remove();
        }

        this.scrollToBottom();
    }

    mostrarVentanaReporte(datos, tipoReporte) {
        const ventanaReporte = document.createElement('div');
        ventanaReporte.className = 'ventana-reporte';
        
        ventanaReporte.innerHTML = `
            <h2>Reporte: ${tipoReporte}</h2>
            ${this.crearTablaDesdeVatos(datos)}
            <button id="descargar-reporte">Descargar Reporte</button>
            <button id="cerrar-reporte">Cerrar</button>
        `;

        document.body.appendChild(ventanaReporte);

        document.getElementById('descargar-reporte').onclick = () => this.descargarReporte(datos, tipoReporte);
        document.getElementById('cerrar-reporte').onclick = () => ventanaReporte.remove();
    }

    crearTablaDesdeVatos(datos) {
        return `
            <table>
                ${datos.map((fila, index) => `
                    <tr>
                        ${fila.map(celda => `<${index === 0 ? 'th' : 'td'}>${celda}</${index === 0 ? 'th' : 'td'}>`).join('')}
                    </tr>
                `).join('')}
            </table>
        `;
    }

    descargarReporte(datos, tipoReporte) {
        const contenidoCsv = datos.map(fila => fila.join(',')).join('\n');
        const blob = new Blob([contenidoCsv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `reporte_${tipoReporte.replace(/\s+/g, '_')}.csv`;
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
}

// Inicializar el asistente virtual cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
    new AsistenteVirtual();
});

// Export the AsistenteVirtual class
export default AsistenteVirtual;