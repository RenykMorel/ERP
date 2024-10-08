document.addEventListener('DOMContentLoaded', function() {
    const buscarBtn = document.getElementById('buscar-btn');
    const crearNuevoBtn = document.getElementById('crear-nuevo-btn');
    const bancoForm = document.getElementById('banco-form');
    const bancosTabla = document.getElementById('bancos-tbody');
    const modal = document.querySelector('.modal');

    buscarBtn.addEventListener('click', buscarBancos);
    crearNuevoBtn.addEventListener('click', mostrarFormularioCrearBanco);
    bancoForm.addEventListener('submit', guardarBanco);
    bancosTabla.addEventListener('click', manejarAccionesBanco);

    function buscarBancos() {
        const id = document.getElementById('id-banco').value;
        const nombre = document.getElementById('nombre-banco').value;
        const contacto = document.getElementById('contacto-banco').value;
        const estatus = document.getElementById('estatus-banco').value;
    
        console.log(`Buscando bancos con criterios: id=${id}, nombre=${nombre}, contacto=${contacto}, estatus=${estatus}`);
    
        fetch(`/api/buscar-bancos?id=${id}&nombre=${nombre}&contacto=${contacto}&estatus=${estatus}`)
            .then(handleResponse)
            .then(bancos => {
                console.log(`Se encontraron ${bancos.length} bancos`);
                actualizarTablaBancos(bancos);
            })
            .catch(handleError);
    }

    function actualizarTablaBancos(bancos) {
        bancosTabla.innerHTML = '';
        bancos.forEach(banco => {
            console.log(`Añadiendo banco a la tabla: ID=${banco.id}, Nombre=${banco.nombre}`);
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${banco.id}</td>
                <td class="font-medium">${banco.nombre}</td>
                <td>${banco.telefono}</td>
                <td>${banco.contacto}</td>
                <td>${banco.telefono_contacto}</td>
                <td>
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${banco.estatus === 'activo' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${banco.estatus}
                    </span>
                </td>
                <td class="whitespace-nowrap text-sm font-medium">
                    <button class="editar-banco text-blue-600 hover:text-blue-900 mr-2" data-id="${banco.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="eliminar-banco text-red-600 hover:text-red-900 mr-2" data-id="${banco.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="cambiar-estatus-banco ${banco.estatus === 'activo' ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'}" data-id="${banco.id}" data-estatus="${banco.estatus}">
                        <i class="fas ${banco.estatus === 'activo' ? 'fa-toggle-off' : 'fa-toggle-on'}"></i>
                    </button>
                </td>
            `;
            bancosTabla.appendChild(tr);
        });
    }
    
    function mostrarFormularioCrearBanco() {
        console.log('Mostrando formulario para crear nuevo banco');
        bancoForm.reset();
        bancoForm.querySelector('[name="id"]').value = '';
        document.getElementById('modal-title').textContent = 'Crear Nuevo Banco';
        toggleModal();
    }

    function guardarBanco(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const bancoData = Object.fromEntries(formData.entries());
        const id = bancoData.id;
        delete bancoData.id;
    
        console.log(`${id ? 'Actualizando' : 'Creando'} banco con datos:`, bancoData);
    
        const url = id ? `/api/actualizar-banco/${id}` : '/api/crear-banco';
        const method = id ? 'PUT' : 'POST';
    
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bancoData),
        })
        .then(handleResponse)
        .then(data => {
            console.log(`Banco ${id ? 'actualizado' : 'creado'} exitosamente:`, data);
            Swal.fire({
                title: '¡Éxito!',
                text: id ? 'Banco actualizado correctamente' : 'Banco creado correctamente',
                icon: 'success',
                confirmButtonText: 'OK'
            });
            buscarBancos();
            toggleModal();
        })
        .catch(handleError);
    }

    function manejarAccionesBanco(e) {
        const target = e.target.closest('button');
        if (!target) return;

        const id = target.dataset.id;
        if (target.classList.contains('editar-banco')) {
            editarBanco(id);
        } else if (target.classList.contains('eliminar-banco')) {
            eliminarBanco(id);
        } else if (target.classList.contains('cambiar-estatus-banco')) {
            cambiarEstatus(id, target.dataset.estatus);
        }
    }

    function editarBanco(id) {
        console.log(`Editando banco con ID: ${id}`);
        fetch(`/api/obtener-banco/${id}`)
            .then(handleResponse)
            .then(banco => {
                console.log('Datos del banco obtenidos:', banco);
                for (let key in banco) {
                    if (bancoForm.elements[key]) {
                        bancoForm.elements[key].value = banco[key];
                    }
                }
                document.getElementById('modal-title').textContent = 'Editar Banco';
                toggleModal();
            })
            .catch(handleError);
    }

    function eliminarBanco(id) {
        console.log(`Iniciando proceso de eliminación del banco con ID: ${id}`);
        Swal.fire({
            title: '¿Estás seguro?',
            text: "No podrás revertir esta acción",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                console.log(`Confirmada la eliminación del banco con ID: ${id}`);
                fetch(`/api/eliminar-banco/${id}`, { method: 'DELETE' })
                    .then(handleResponse)
                    .then(data => {
                        console.log('Banco eliminado exitosamente:', data);
                        buscarBancos();
                        Swal.fire('Eliminado', 'El banco ha sido eliminado', 'success');
                    })
                    .catch(handleError);
            } else {
                console.log(`Cancelada la eliminación del banco con ID: ${id}`);
            }
        });
    }

    function cambiarEstatus(id, estatusActual) {
        const nuevoEstatus = estatusActual === 'activo' ? 'inactivo' : 'activo';
        console.log(`Cambiando estatus del banco ${id} de ${estatusActual} a ${nuevoEstatus}`);
        fetch(`/api/cambiar-estatus-banco/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ estatus: nuevoEstatus }),
        })
        .then(handleResponse)
        .then(data => {
            console.log(`Estatus del banco ${id} cambiado exitosamente a ${nuevoEstatus}`);
            buscarBancos();
            Swal.fire('Éxito', `Estatus del banco cambiado a ${nuevoEstatus}`, 'success');
        })
        .catch(handleError);
    }

    function handleResponse(response) {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    }

    function handleError(error) {
        console.error('Error:', error);
        Swal.fire({
            title: 'Error',
            text: error.error || 'Ocurrió un error inesperado',
            icon: 'error',
            confirmButtonText: 'OK'
        });
    }

    function toggleModal() {
        modal.classList.toggle('hidden');
    }

    // Event listeners para cerrar el modal
    document.querySelectorAll('.modal-close, .modal-overlay').forEach(element => {
        element.addEventListener('click', toggleModal);
    });

    // Evitar que el clic dentro del contenido del modal lo cierre
    modal.querySelector('.modal-container').addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // Cargar bancos al iniciar la página
    console.log('Cargando bancos al iniciar la página');
    buscarBancos();
});