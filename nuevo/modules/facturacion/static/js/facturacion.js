document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const facturasList = document.getElementById('facturas-tbody');
    const facturaForm = document.getElementById('factura-form');
    const facturaModal = document.querySelector('.modal');
    const modalTitle = document.getElementById('modal-title');
    const nuevaFacturaBtn = document.getElementById('crear-nuevo-btn');
    const buscarFacturasBtn = document.getElementById('buscar-btn');
    const modalCloseButtons = document.querySelectorAll('.modal-close');

    // Event Listeners
    if (nuevaFacturaBtn) {
        nuevaFacturaBtn.addEventListener('click', () => mostrarModal());
    }
    modalCloseButtons.forEach(btn => btn.addEventListener('click', ocultarModal));
    if (facturaForm) {
        facturaForm.addEventListener('submit', manejarEnvioFormulario);
    }
    if (buscarFacturasBtn) {
        buscarFacturasBtn.addEventListener('click', buscarFacturas);
    }

    // Funciones
    function mostrarModal(facturaId = null) {
        modalTitle.textContent = facturaId ? 'Editar Factura' : 'Crear Nueva Factura';
        if (facturaId) {
            cargarDatosFactura(facturaId);
        } else {
            facturaForm.reset();
        }
        toggleModal();
    }

    function ocultarModal() {
        toggleModal();
        facturaForm.reset();
    }

    function toggleModal() {
        facturaModal.classList.toggle('opacity-0');
        facturaModal.classList.toggle('pointer-events-none');
        document.body.classList.toggle('modal-active');
    }

    function cargarDatosFactura(id) {
        fetch(`/api/obtener-factura/${id}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('factura-form').id.value = data.id;
                document.getElementById('factura-form').numero.value = data.numero;
                document.getElementById('factura-form').cliente.value = data.cliente;
                document.getElementById('factura-form').fecha.value = data.fecha;
                document.getElementById('factura-form').total.value = data.total;
                document.getElementById('factura-form').estatus.value = data.estatus;
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error', 'No se pudo cargar la información de la factura', 'error');
            });
    }

    function manejarEnvioFormulario(e) {
        e.preventDefault();
        if (!validarFormulario()) {
            return;
        }

        const formData = new FormData(facturaForm);
        const facturaData = Object.fromEntries(formData);
        const facturaId = facturaData.id;
        const url = facturaId ? `/api/actualizar-factura/${facturaId}` : '/api/crear-factura';
        const method = facturaId ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            body: JSON.stringify(facturaData),
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            Swal.fire('Éxito', facturaId ? 'Factura actualizada correctamente' : 'Factura creada correctamente', 'success');
            ocultarModal();
            buscarFacturas();
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', error.message || 'Ocurrió un error al guardar la factura', 'error');
        });
    }

    function validarFormulario() {
        let esValido = true;
        ['numero', 'cliente', 'fecha', 'total', 'estatus'].forEach(campo => {
            const elemento = document.getElementById('factura-form')[campo];
            if (!elemento.value.trim()) {
                marcarError(elemento, `El campo ${campo} es requerido`);
                esValido = false;
            } else {
                limpiarError(elemento);
            }
        });
        return esValido;
    }

    function marcarError(elemento, mensaje) {
        elemento.classList.add('border-red-500');
        const mensajeError = document.createElement('p');
        mensajeError.textContent = mensaje;
        mensajeError.classList.add('text-red-500', 'text-xs', 'italic', 'mt-1');
        elemento.parentNode.appendChild(mensajeError);
    }

    function limpiarError(elemento) {
        elemento.classList.remove('border-red-500');
        const mensajeError = elemento.parentNode.querySelector('.text-red-500');
        if (mensajeError) {
            mensajeError.remove();
        }
    }

    function buscarFacturas() {
        const numero = document.getElementById('numero-factura').value;
        const cliente = document.getElementById('cliente-factura').value;
        const fecha = document.getElementById('fecha-factura').value;
        const estatus = document.getElementById('estatus-factura').value;
    
        fetch(`/api/buscar-facturas?numero=${numero}&cliente=${cliente}&fecha=${fecha}&estatus=${estatus}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return response.json();
            })
            .then(data => actualizarTablaFacturas(data))
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error', 'Ocurrió un error al buscar facturas', 'error');
            });
    }

    function actualizarTablaFacturas(facturas) {
        const tbody = document.getElementById('facturas-tbody');
        tbody.innerHTML = '';
        facturas.forEach(factura => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${factura.numero}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${factura.cliente}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${factura.fecha}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${factura.total}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getEstatusColor(factura.estatus)}">
                        ${factura.estatus}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button class="editar-factura text-blue-600 hover:text-blue-900 mr-2" data-id="${factura.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="eliminar-factura text-red-600 hover:text-red-900 mr-2" data-id="${factura.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="cambiar-estatus-factura text-yellow-600 hover:text-yellow-900" data-id="${factura.id}" data-estatus="${factura.estatus}">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    function getEstatusColor(estatus) {
        switch (estatus) {
            case 'pendiente':
                return 'bg-yellow-100 text-yellow-800';
            case 'pagada':
                return 'bg-green-100 text-green-800';
            case 'anulada':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    // Funciones globales (accesibles desde HTML)
    window.editarFactura = function(id) {
        mostrarModal(id);
    };

    window.eliminarFactura = function(id) {
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
                fetch(`/api/eliminar-factura/${id}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.message) {
                            Swal.fire('Eliminado', data.message, 'success');
                            buscarFacturas();
                        } else {
                            Swal.fire('Error', data.error, 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        Swal.fire('Error', 'Ocurrió un error al eliminar la factura', 'error');
                    });
            }
        });
    };

    window.cambiarEstatusFactura = function(id, estatusActual) {
        Swal.fire({
            title: 'Cambiar Estatus',
            input: 'select',
            inputOptions: {
                'pendiente': 'Pendiente',
                'pagada': 'Pagada',
                'anulada': 'Anulada'
            },
            inputValue: estatusActual,
            showCancelButton: true,
            confirmButtonText: 'Cambiar',
            cancelButtonText: 'Cancelar',
            inputValidator: (value) => {
                if (!value) {
                    return 'Debes seleccionar un estatus';
                }
            }
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(`/api/cambiar-estatus-factura/${id}`, {
                    method: 'PUT',
                    body: JSON.stringify({ estatus: result.value }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        Swal.fire('Error', data.error, 'error');
                    } else {
                        Swal.fire('Éxito', `Estatus cambiado a ${result.value}`, 'success');
                        buscarFacturas();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    Swal.fire('Error', 'Ocurrió un error al cambiar el estatus de la factura', 'error');
                });
            }
        });
    };

    // Inicializar
    if (facturasList) {
        buscarFacturas();
    }
});