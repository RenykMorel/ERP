// contabilidad.js

document.addEventListener('DOMContentLoaded', function() {
    initializeContabilidadForms();
});

function initializeContabilidadForms() {
    const cuentaForm = document.getElementById('cuenta-form');
    const asientoForm = document.getElementById('asiento-form');

    if (cuentaForm) {
        cuentaForm.addEventListener('submit', handleCuentaSubmit);
    }

    if (asientoForm) {
        asientoForm.addEventListener('submit', handleAsientoSubmit);
    }
}

function handleCuentaSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    fetch('/contabilidad/crear_cuenta', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Cuenta creada exitosamente');
            event.target.reset();
        } else {
            alert('Error al crear la cuenta: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error al procesar la solicitud');
    });
}

function handleAsientoSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    fetch('/contabilidad/crear_asiento', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Asiento creado exitosamente');
            event.target.reset();
        } else {
            alert('Error al crear el asiento: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ocurrió un error al procesar la solicitud');
    });
}

function cargarBalanceGeneral() {
    fetch('/contabilidad/balance_general')
    .then(response => response.json())
    .then(data => {
        // Aquí puedes actualizar la UI con los datos del balance general
        console.log(data);
    })
    .catch(error => console.error('Error:', error));
}

function cargarEstadoResultados() {
    fetch('/contabilidad/estado_resultados')
    .then(response => response.json())
    .then(data => {
        // Aquí puedes actualizar la UI con los datos del estado de resultados
        console.log(data);
    })
    .catch(error => console.error('Error:', error));
}