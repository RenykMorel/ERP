// facturacion.js

function inicializarModuloFacturacion() {
    console.log('Inicializando módulo de facturación');
    
    // Configurar eventos
    const crearNuevoBtn = document.getElementById('crear-nuevo-btn');
    if (crearNuevoBtn) {
        crearNuevoBtn.addEventListener('click', () => mostrarModal());
    }

    const buscarBtn = document.getElementById('buscar-btn');
    if (buscarBtn) {
        buscarBtn.addEventListener('click', buscarFacturas);
    }

    const facturaForm = document.getElementById('factura-form');
    if (facturaForm) {
        facturaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            manejarEnvioFormulario();
        });
    }

    const modalCloseButtons = document.querySelectorAll('.modal-close');
    modalCloseButtons.forEach(btn => btn.addEventListener('click', ocultarModal));

    // Cargar facturas iniciales
    if (document.getElementById('facturas-tbody')) {
        buscarFacturas();
    }

    // Configurar enlaces de navegación
    document.querySelectorAll('.facturacion-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const submodulo = this.getAttribute('data-submodule');
            cargarSubmodulo(submodulo);
        });
    });
}

function cargarSubmodulo(submodulo) {
    console.log(`Cargando submódulo: ${submodulo}`);
    fetch(`/facturacion/${submodulo}`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('contenido-principal').innerHTML = html;
            inicializarModuloFacturacion();
        })
        .catch(error => console.error('Error al cargar submódulo:', error));
}

function mostrarModal(facturaId = null) {
    const modal = document.getElementById('facturaModal');
    const modalTitle = document.getElementById('modal-title');
    const facturaForm = document.getElementById('factura-form');

    modalTitle.textContent = facturaId ? 'Editar Factura' : 'Crear Nueva Factura';
    
    if (facturaId) {
        cargarDatosFactura(facturaId);
    } else {
        facturaForm.reset();
    }

    modal.style.display = 'block';
}

function ocultarModal() {
    const modal = document.getElementById('facturaModal');
    modal.style.display = 'none';
    document.getElementById('factura-form').reset();
}

function cargarDatosFactura(id) {
    fetch(`/facturacion/api/obtener-factura/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const factura = data.factura;
                const form = document.getElementById('factura-form');
                form.id.value = factura.id;
                form.numero.value = factura.numero;
                form.cliente.value = factura.cliente;
                form.fecha.value = factura.fecha;
                form.total.value = factura.total;
                form.estatus.value = factura.estatus;
            } else {
                throw new Error(data.message || 'Error al cargar los datos de la factura');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('No se pudo cargar la información de la factura');
        });
}

function manejarEnvioFormulario() {
    const form = document.getElementById('factura-form');
    const facturaData = new FormData(form);
    const facturaId = facturaData.get('id');
    const url = facturaId ? `/facturacion/api/actualizar-factura/${facturaId}` : '/facturacion/api/crear-factura';
    const method = facturaId ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        body: JSON.stringify(Object.fromEntries(facturaData)),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obtenerCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(facturaId ? 'Factura actualizada correctamente' : 'Factura creada correctamente');
            ocultarModal();
            buscarFacturas();
        } else {
            throw new Error(data.message || 'Error al procesar la factura');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error al guardar la factura: ' + error.message);
    });
}

function buscarFacturas() {
    const numero = document.getElementById('numero-factura').value;
    const cliente = document.getElementById('cliente-factura').value;
    const fecha = document.getElementById('fecha-factura').value;
    const estatus = document.getElementById('estatus-factura').value;

    fetch(`/facturacion/api/buscar-facturas?numero=${numero}&cliente=${cliente}&fecha=${fecha}&estatus=${estatus}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                actualizarTablaFacturas(data.facturas);
            } else {
                throw new Error(data.message || 'Error al buscar facturas');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al buscar facturas');
        });
}

function actualizarTablaFacturas(facturas) {
    const tbody = document.getElementById('facturas-tbody');
    tbody.innerHTML = '';
    facturas.forEach(factura => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${factura.numero}</td>
            <td>${factura.cliente}</td>
            <td>${factura.fecha}</td>
            <td>${factura.total}</td>
            <td>${factura.estatus}</td>
            <td>
                <button onclick="editarFactura(${factura.id})" class="btn btn-sm btn-info">Editar</button>
                <button onclick="eliminarFactura(${factura.id})" class="btn btn-sm btn-danger">Eliminar</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function editarFactura(id) {
    mostrarModal(id);
}

function eliminarFactura(id) {
    if (confirm('¿Estás seguro de que quieres eliminar esta factura?')) {
        fetch(`/facturacion/api/eliminar-factura/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': obtenerCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Factura eliminada correctamente');
                buscarFacturas();
            } else {
                throw new Error(data.message || 'Error al eliminar la factura');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al eliminar la factura');
        });
    }
}

function obtenerCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Inicializar el módulo cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', inicializarModuloFacturacion);