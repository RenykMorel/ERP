// asistente-virtual.js

const AsistenteVirtual = (function() {
    let conversationHistory = [];
    let asistenteActivo = false;
    let bienvenidaMostrada = false;

    const chatWindow = document.getElementById('chat-window');
    const chatMessages = document.getElementById('chat-messages');
    const asistenteInput = document.getElementById('assistant-input');
    const asistenteEnviar = document.getElementById('assistant-send');

    function initialize() {
        conversationHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
        bienvenidaMostrada = localStorage.getItem('bienvenidaMostrada') === 'true';

        cargarHistorialConversacion();
        verificarEstadoAsistente();
        setupEventListeners();
    }

    function cargarHistorialConversacion() {
        chatMessages.innerHTML = '';
        conversationHistory.forEach(entry => {
            const mensajeElement = document.createElement('p');
            mensajeElement.className = entry.sender === 'Usuario' ? 'user-message' : 'assistant-message';
            mensajeElement.textContent = `${entry.sender}: ${entry.message}`;
            chatMessages.appendChild(mensajeElement);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function verificarEstadoAsistente() {
        fetch('/api/asistente_status')
            .then(response => response.json())
            .then(data => {
                console.log('Estado del asistente:', data);
                asistenteActivo = data.activo;
                if (asistenteActivo && !bienvenidaMostrada) {
                    mostrarMensajeBienvenida();
                }
            })
            .catch(error => {
                console.error('Error al verificar el estado del asistente:', error);
                chatWindow.classList.add('asistente-inactivo');
                mostrarMensajeAsistente("Error al verificar el estado del asistente. Por favor, intente más tarde.");
            });
    }

    function setupEventListeners() {
        if (asistenteInput && asistenteEnviar) {
            asistenteEnviar.addEventListener('click', enviarMensaje);
            asistenteInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    enviarMensaje();
                }
            });
        }
    }

    function enviarMensaje() {
        const pregunta = asistenteInput.value.trim();
        if (pregunta) {
            mostrarMensajeUsuario(pregunta);
            notificarAsistente(pregunta);
            asistenteInput.value = '';
        }
    }

    function mostrarMensajeUsuario(mensaje) {
        const nuevoMensaje = document.createElement('p');
        nuevoMensaje.textContent = `Tú: ${mensaje}`;
        nuevoMensaje.className = 'user-message';
        chatMessages.appendChild(nuevoMensaje);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        conversationHistory.push({ sender: 'Usuario', message: mensaje });
        localStorage.setItem('chatHistory', JSON.stringify(conversationHistory));
    }

    function mostrarMensajeAsistente(mensaje) {
        const nuevoMensaje = document.createElement('p');
        nuevoMensaje.textContent = `Asistente: ${mensaje}`;
        nuevoMensaje.className = 'assistant-message';
        chatMessages.appendChild(nuevoMensaje);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        conversationHistory.push({ sender: 'Asistente', message: mensaje });
        localStorage.setItem('chatHistory', JSON.stringify(conversationHistory));
    }

    function mostrarMensajeBienvenida() {
        const mensajeBienvenida = "¡Hola! Soy tu asistente virtual de CalculAI. ¿En qué puedo ayudarte hoy?";
        mostrarMensajeAsistente(mensajeBienvenida);
        bienvenidaMostrada = true;
        localStorage.setItem('bienvenidaMostrada', 'true');
    }

    function notificarAsistente(mensaje) {
        const paginaActual = window.location.pathname;
        
        fetch('/api/asistente', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                pregunta: mensaje,
                pagina_actual: paginaActual
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.tipo === 'archivos') {
                mostrarMensajeConArchivos(data.mensaje, data.archivos);
            } else if (data.tipo === 'texto') {
                mostrarMensajeAsistente(data.respuesta);
            } else {
                console.error('Respuesta inesperada del asistente:', data);
                mostrarMensajeAsistente("Lo siento, ocurrió un error al procesar tu solicitud.");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensajeAsistente("Ocurrió un error al comunicarse con el asistente.");
        });
    }

    function resetConversacion() {
        localStorage.removeItem('chatHistory');
        localStorage.removeItem('bienvenidaMostrada');
        conversationHistory = [];
        chatMessages.innerHTML = '';
        bienvenidaMostrada = false;
        initialize();
    }

    return {
        initialize: initialize,
        resetConversacion: resetConversacion,
        mostrarMensajeAsistente: mostrarMensajeAsistente
    };
})();

// Exportar el módulo para uso en otros archivos
export default AsistenteVirtual;