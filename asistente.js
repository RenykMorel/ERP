// asistente.js
const ASISTENTE_ACTIVO = true; // Esto debería venir de tu configuración o backend

function initializeAsistente() {
    const chatWindow = document.getElementById('chat-window');
    const asistenteInput = document.getElementById('asistente-input');
    const asistenteEnviar = document.getElementById('asistente-enviar');

    if (!ASISTENTE_ACTIVO) {
        chatWindow.classList.add('asistente-inactivo');
        mostrarMensajeAsistente("El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.");
    }

    if (asistenteInput && asistenteEnviar) {
        asistenteEnviar.addEventListener('click', () => {
            const pregunta = asistenteInput.value.trim();
            if (pregunta) {
                notificarAsistente(pregunta);
                asistenteInput.value = '';
            }
        });

        asistenteInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                asistenteEnviar.click();
            }
        });
    }
}

function mostrarMensajeAsistente(mensaje) {
    const mensajesDiv = document.getElementById('asistente-mensajes');
    if (mensajesDiv) {
        const nuevoMensaje = document.createElement('p');
        if (mensaje === "El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.") {
            nuevoMensaje.classList.add('asistente-inactivo');
            nuevoMensaje.innerHTML = `
                <span>El asistente no está activo.</span>
                <span>Por favor, contacte al <span class="highlight">equipo de CalculAI</span> para su activación.</span>
            `;
        } else {
            nuevoMensaje.textContent = mensaje;
        }
        mensajesDiv.appendChild(nuevoMensaje);
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }
}

function notificarAsistente(mensaje) {
    if (!ASISTENTE_ACTIVO) {
        mostrarMensajeAsistente("El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.");
        return;
    }

    // Aquí iría tu lógica para enviar mensajes al asistente cuando esté activo
    // Por ahora, simplemente mostramos el mensaje
    mostrarMensajeAsistente(mensaje);
}

// Inicializar el asistente cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', initializeAsistente);