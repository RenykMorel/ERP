document.addEventListener('DOMContentLoaded', function() {
    const buscarBtn = document.getElementById('buscar-btn');
    const crearNuevoBtn = document.getElementById('crear-nuevo-btn');
    const crearBancoForm = document.getElementById('crear-banco-form');
    const nuevoBancoForm = document.getElementById('nuevo-banco-form');
    const cancelarCrearBtn = document.getElementById('cancelar-crear');
    const bancosTabla = document.getElementById('bancos-tbody');

    buscarBtn.addEventListener('click', buscarBancos);
    crearNuevoBtn.addEventListener('click', mostrarFormularioCrearBanco);
    nuevoBancoForm.addEventListener('submit', guardarBanco);
    cancelarCrearBtn.addEventListener('click', ocultarFormularioCrearBanco);
    bancosTabla.addEventListener('click', manejarAccionesBanco);

    function buscarBancos() {
        const id = document.getElementById('id-banco').value;
        const nombre = document.getElementById('nombre-banco').value;
        const contacto = document.getElementById('contacto-banco').value;
        const estatus = document.getElementById('estatus-banco').value;

        fetch(`/banco/api/buscar-bancos?id=${id}&nombre=${nombre}&contacto=${contacto}&estatus=${estatus}`)
            .then(response => response.json())
            .then(bancos => {
                actualizarTablaBancos(bancos);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al buscar bancos');
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
                    <button class="cambiar-estatus" data-id="${banco.id}" data-estatus="${banco.estatus}">
                        ${banco.estatus === 'activo' ? 'Desactivar' : 'Activar'}
                    </button>
                </td>
            `;
            bancosTabla.appendChild(tr);
        });
    }

    function mostrarFormularioCrearBanco() {
        crearBancoForm.style.display = 'block';
        nuevoBancoForm.reset();
        nuevoBancoForm.querySelector('[name="id"]').value = '';
        document.getElementById('form-title').textContent = 'Crear Nuevo Banco';
    }

    function ocultarFormularioCrearBanco() {
        crearBancoForm.style.display = 'none';
    }

    function guardarBanco(e) {
        e.preventDefault();
        const formData = new FormData(nuevoBancoForm);
        const bancoData = Object.fromEntries(formData.entries());
        const id = bancoData.id;
        delete bancoData.id;

        const url = id ? `/banco/api/actualizar-banco/${id}` : '/banco/api/crear-banco';
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
        .then(nuevoBanco => {
            buscarBancos();
            ocultarFormularioCrearBanco();
            alert(id ? 'Banco actualizado correctamente' : 'Banco creado correctamente');
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.error || 'Ocurrió un error al guardar el banco');
        });
    }

    function manejarAccionesBanco(e) {
        if (e.target.classList.contains('editar-banco')) {
            const bancoId = e.target.dataset.id;
            editarBanco(bancoId);
        } else if (e.target.classList.contains('eliminar-banco')) {
            const bancoId = e.target.dataset.id;
            eliminarBanco(bancoId);
        } else if (e.target.classList.contains('cambiar-estatus')) {
            const bancoId = e.target.dataset.id;
            const estatusActual = e.target.dataset.estatus;
            cambiarEstatus(bancoId, estatusActual);
        }
    }

    function editarBanco(id) {
        fetch(`/banco/api/obtener-banco/${id}`)
            .then(response => response.json())
            .then(banco => {
                nuevoBancoForm.querySelector('[name="id"]').value = banco.id;
                nuevoBancoForm.querySelector('[name="nombre"]').value = banco.nombre;
                nuevoBancoForm.querySelector('[name="telefono"]').value = banco.telefono;
                nuevoBancoForm.querySelector('[name="contacto"]').value = banco.contacto;
                nuevoBancoForm.querySelector('[name="telefono_contacto"]').value = banco.telefono_contacto;
                nuevoBancoForm.querySelector('[name="estatus"]').value = banco.estatus;
                
                crearBancoForm.style.display = 'block';
                document.getElementById('form-title').textContent = 'Editar Banco';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al cargar los datos del banco');
            });
    }

    function eliminarBanco(id) {
        if (confirm('¿Estás seguro de que deseas eliminar este banco?')) {
            fetch(`/banco/api/eliminar-banco/${id}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    buscarBancos();
                    alert('Banco eliminado correctamente');
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al eliminar el banco');
                });
        }
    }

    function cambiarEstatus(id, estatusActual) {
        const nuevoEstatus = estatusActual === 'activo' ? 'inactivo' : 'activo';
        fetch(`/banco/api/cambiar-estatus-banco/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ estatus: nuevoEstatus }),
        })
        .then(response => response.json())
        .then(data => {
            buscarBancos();
            alert(`Estatus del banco cambiado a ${nuevoEstatus}`);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estatus del banco');
        });
    }

    // Cargar bancos al iniciar la página
    buscarBancos();
});