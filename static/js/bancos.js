document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const buscarBtn = document.getElementById('buscar-btn');
    const crearNuevoBtn = document.getElementById('crear-nuevo-btn');
    const crearBancoForm = document.getElementById('crear-banco-form');
    const nuevoBancoForm = document.getElementById('nuevo-banco-form');
    const cancelarCrearBtn = document.getElementById('cancelar-crear');
    const bancosTabla = document.getElementById('bancos-tbody');

    // Event Listeners
    buscarBtn.addEventListener('click', buscarBancos);
    crearNuevoBtn.addEventListener('click', mostrarFormularioCrearBanco);
    nuevoBancoForm.addEventListener('submit', crearBanco);
    cancelarCrearBtn.addEventListener('click', ocultarFormularioCrearBanco);
    bancosTabla.addEventListener('click', manejarAccionesBanco);

    // Notificar al asistente que el usuario ha accedido a la página de Bancos
    notificarAsistente("El usuario ha accedido a la página de Bancos");

    function buscarBancos() {
        const id = document.getElementById('id-banco').value;
        const nombre = document.getElementById('nombre-banco').value;
        const contacto = document.getElementById('contacto-banco').value;
        const estatus = document.getElementById('estatus-banco').value;

        fetch(`/api/buscar-bancos?id=${id}&nombre=${nombre}&contacto=${contacto}&estatus=${estatus}`)
            .then(response => response.json())
            .then(bancos => {
                actualizarTablaBancos(bancos);
                notificarAsistente(`Se ha realizado una búsqueda de bancos con los siguientes criterios: ID=${id}, Nombre=${nombre}, Contacto=${contacto}, Estatus=${estatus}`);
            })
            .catch(error => {
                console.error('Error:', error);
                notificarAsistente(`Ha ocurrido un error al buscar bancos: ${error}`);
            });
    }

    function actualizarTablaBancos(bancos) {
        bancosTabla.innerHTML = '';
        bancos.forEach(banco => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${banco.id}</td>
                <td>${banco.nombre}</td>
                <td>${banco.telefono}</td>
                <td>${banco.contacto}</td>
                <td>${banco.telefono_contacto}</td>
                <td>${banco.estatus}</td>
                <td>
                    <button class="editar-banco" data-id="${banco.id}">Editar</button>
                    <button class="eliminar-banco" data-id="${banco.id}">Eliminar</button>
                </td>
            `;
            bancosTabla.appendChild(tr);
        });
    }

    function mostrarFormularioCrearBanco() {
        crearBancoForm.style.display = 'block';
        notificarAsistente("El usuario ha iniciado el proceso de creación de un nuevo banco");
    }

    function ocultarFormularioCrearBanco() {
        crearBancoForm.style.display = 'none';
        nuevoBancoForm.reset();
    }

    function crearBanco(e) {
        e.preventDefault();
        const formData = new FormData(nuevoBancoForm);
        const bancoData = Object.fromEntries(formData.entries());

        fetch('/api/crear-banco', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bancoData),
        })
        .then(response => response.json())
        .then(nuevoBanco => {
            buscarBancos(); // Actualizar la lista de bancos
            ocultarFormularioCrearBanco();
            notificarAsistente(`Se ha creado un nuevo banco con el nombre: ${nuevoBanco.nombre}`);
        })
        .catch(error => {
            console.error('Error:', error);
            notificarAsistente(`Ha ocurrido un error al crear el banco: ${error}`);
        });
    }

    function manejarAccionesBanco(e) {
        if (e.target.classList.contains('editar-banco')) {
            const bancoId = e.target.dataset.id;
            editarBanco(bancoId);
        } else if (e.target.classList.contains('eliminar-banco')) {
            const bancoId = e.target.dataset.id;
            eliminarBanco(bancoId);
        }
    }

    function editarBanco(id) {
        // Aquí implementarías la lógica para editar un banco
        console.log('Editar banco:', id);
        notificarAsistente(`El usuario ha iniciado la edición del banco con ID: ${id}`);
    }

    function eliminarBanco(id) {
        if (confirm('¿Estás seguro de que deseas eliminar este banco?')) {
            fetch(`/api/eliminar-banco/${id}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    buscarBancos(); // Actualizar la lista de bancos
                    notificarAsistente(`Se ha eliminado el banco con ID: ${id}`);
                })
                .catch(error => {
                    console.error('Error:', error);
                    notificarAsistente(`Ha ocurrido un error al eliminar el banco: ${error}`);
                });
        }
    }

    function notificarAsistente(mensaje) {
        fetch('/api/asistente', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pregunta: mensaje })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del asistente:', data.respuesta);
            mostrarMensajeAsistente(data.respuesta);
        })
        .catch(error => console.error('Error:', error));
    }

    function mostrarMensajeAsistente(mensaje) {
        const mensajesDiv = document.getElementById('asistente-mensajes');
        const nuevoMensaje = document.createElement('p');
        nuevoMensaje.textContent = mensaje;
        mensajesDiv.appendChild(nuevoMensaje);
    }

    // Manejar preguntas al asistente
    const asistenteEnviarBtn = document.getElementById('asistente-enviar');
    const asistenteInput = document.getElementById('asistente-input');

    asistenteEnviarBtn.addEventListener('click', function() {
        const pregunta = asistenteInput.value;
        if (pregunta) {
            notificarAsistente(pregunta);
            asistenteInput.value = '';
        }
    });

    // Cargar bancos al iniciar la página
    buscarBancos();
});