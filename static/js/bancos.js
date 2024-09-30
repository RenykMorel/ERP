document.addEventListener('DOMContentLoaded', function() {
    const buscarBtn = document.getElementById('buscar-btn');
    const crearNuevoBtn = document.getElementById('crear-nuevo-btn');
    const bancoForm = document.getElementById('banco-form');
    const bancosTabla = document.getElementById('bancos-tbody');

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
            .then(response => response.json())
            .then(bancos => {
                console.log(`Se encontraron ${bancos.length} bancos`);
                actualizarTablaBancos(bancos);
            })
            .catch(error => {
                console.error('Error al buscar bancos:', error);
                Swal.fire('Error', 'Error al buscar bancos', 'error');
            });
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
                    <span class="px-1 inline-flex text-xs leading-5 font-semibold rounded-full ${banco.estatus === 'activo' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${banco.estatus}
                    </span>
                </td>
                <td class="whitespace-nowrap text-sm font-medium">
                    <button class="editar-banco text-blue-600 hover:text-blue-900" data-id="${banco.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="eliminar-banco text-red-600 hover:text-red-900" data-id="${banco.id}">
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
        document.getElementById('form-title').textContent = 'Crear Nuevo Banco';
        // Aquí deberías mostrar el formulario (por ejemplo, un modal)
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
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            console.log(`Banco ${id ? 'actualizado' : 'creado'} exitosamente:`, data);
            Swal.fire({
                title: '¡Éxito!',
                text: id ? 'Banco actualizado correctamente' : 'Banco creado correctamente',
                icon: 'success',
                confirmButtonText: 'OK'
            });
            buscarBancos();
            // Aquí deberías ocultar el formulario
        })
        .catch(error => {
            console.error(`Error al ${id ? 'actualizar' : 'crear'} banco:`, error);
            Swal.fire({
                title: 'Error',
                text: error.error || 'Ocurrió un error al guardar el banco',
                icon: 'error',
                confirmButtonText: 'OK'
            });
        });
    }

    function manejarAccionesBanco(e) {
        if (e.target.classList.contains('editar-banco')) {
            editarBanco(e.target.dataset.id);
        } else if (e.target.classList.contains('eliminar-banco')) {
            eliminarBanco(e.target.dataset.id);
        } else if (e.target.classList.contains('cambiar-estatus')) {
            cambiarEstatus(e.target.dataset.id, e.target.dataset.estatus);
        }
    }

    function editarBanco(id) {
        console.log(`Editando banco con ID: ${id}`);
        fetch(`/api/obtener-banco/${id}`)
            .then(response => response.json())
            .then(banco => {
                console.log('Datos del banco obtenidos:', banco);
                for (let key in banco) {
                    if (bancoForm.elements[key]) {
                        bancoForm.elements[key].value = banco[key];
                    }
                }
                document.getElementById('form-title').textContent = 'Editar Banco';
                // Aquí deberías mostrar el formulario
            })
            .catch(error => {
                console.error('Error al cargar los datos del banco:', error);
                Swal.fire('Error', 'Error al cargar los datos del banco', 'error');
            });
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
            confirmButtonText: 'Sí, eliminar'
        }).then((result) => {
            if (result.isConfirmed) {
                console.log(`Confirmada la eliminación del banco con ID: ${id}`);
                fetch(`/api/eliminar-banco/${id}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Banco eliminado exitosamente:', data);
                        buscarBancos();
                        Swal.fire('Eliminado', 'El banco ha sido eliminado', 'success');
                    })
                    .catch(error => {
                        console.error('Error al eliminar el banco:', error);
                        Swal.fire('Error', 'Error al eliminar el banco', 'error');
                    });
            } else {
                console.log(`Cancelada la eliminación del banco con ID: ${id}`);
            }
        });
    }

    function crearBanco(datos) {
        console.log('Creando nuevo banco con datos:', datos);
        fetch('/api/crear-banco', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(datos)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            console.log('Banco creado exitosamente:', data);
            // Cerrar el modal si existe
            if (typeof toggleModal === 'function') {
                toggleModal();
            }
            // Mostrar mensaje de éxito
            Swal.fire({
                title: '¡Éxito!',
                text: data.message,
                icon: 'success',
                confirmButtonText: 'OK'
            });
            // Agregar el nuevo banco a la tabla
            agregarBancoATabla(data.banco);
            // Limpiar el formulario
            document.getElementById('banco-form').reset();
        })
        .catch(error => {
            console.error('Error al crear el banco:', error.message);
            Swal.fire({
                title: 'Error',
                text: error.message,
                icon: 'error',
                confirmButtonText: 'OK'
            });
        });
    }
    
    function agregarBancoATabla(banco) {
        console.log('Agregando nuevo banco a la tabla:', banco);
        const tbody = document.getElementById('bancos-tbody');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${banco.id}</td>
            <td class="font-medium">${banco.nombre}</td>
            <td>${banco.telefono}</td>
            <td>${banco.contacto}</td>
            <td>${banco.telefono_contacto}</td>
            <td>
                <span class="px-1 inline-flex text-xs leading-5 font-semibold rounded-full ${banco.estatus === 'activo' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${banco.estatus}
                </span>
            </td>
            <td class="whitespace-nowrap text-sm font-medium">
                <button class="editar-banco text-blue-600 hover:text-blue-900" data-id="${banco.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="eliminar-banco text-red-600 hover:text-red-900" data-id="${banco.id}">
                    <i class="fas fa-trash"></i>
                </button>
                <button class="cambiar-estatus-banco ${banco.estatus === 'activo' ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'}" data-id="${banco.id}" data-estatus="${banco.estatus}">
                    <i class="fas ${banco.estatus === 'activo' ? 'fa-toggle-off' : 'fa-toggle-on'}"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    }
    
    // Asegúrate de que esta función se llame cuando se envíe el formulario de creación de banco
    document.getElementById('banco-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const datos = Object.fromEntries(formData);
        crearBanco(datos);
    });

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
        .then(response => response.json())
        .then(data => {
            console.log(`Estatus del banco ${id} cambiado exitosamente a ${nuevoEstatus}`);
            buscarBancos();
            Swal.fire('Éxito', `Estatus del banco cambiado a ${nuevoEstatus}`, 'success');
        })
        .catch(error => {
            console.error(`Error al cambiar el estatus del banco ${id}:`, error);
            Swal.fire('Error', 'Error al cambiar el estatus del banco', 'error');
        });
    }

    // Cargar bancos al iniciar la página
    console.log('Cargando bancos al iniciar la página');
    buscarBancos();
});