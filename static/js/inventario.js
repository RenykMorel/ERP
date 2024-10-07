document.addEventListener('DOMContentLoaded', function() {
    // Inicialización de componentes
    initializeItemsTable();
    initializeEntradaAlmacen();
    initializeSalidaAlmacen();
    initializeInventarioActual();
    initializeReporteInventario();

    // Event listeners para los botones de navegación
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            showSection(targetId);
        });
    });
});

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById(sectionId).style.display = 'block';
}

function initializeItemsTable() {
    fetch('/inventario/api/items')
        .then(response => response.json())
        .then(items => {
            const tableBody = document.querySelector('#items-table tbody');
            tableBody.innerHTML = '';
            items.forEach(item => {
                const row = `
                    <tr>
                        <td>${item.codigo}</td>
                        <td>${item.nombre}</td>
                        <td>${item.tipo}</td>
                        <td>${item.categoria}</td>
                        <td>${item.precio}</td>
                        <td>${item.stock}</td>
                        <td>
                            <button onclick="editItem(${item.id})">Editar</button>
                            <button onclick="deleteItem(${item.id})">Eliminar</button>
                        </td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => console.error('Error:', error));
}

function initializeEntradaAlmacen() {
    const form = document.getElementById('entrada-almacen-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {
            items: [{
                item_id: formData.get('item_id'),
                cantidad: parseInt(formData.get('cantidad'))
            }]
        };
        fetch('/inventario/api/entrada-almacen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            alert(result.message);
            form.reset();
            initializeInventarioActual();
        })
        .catch(error => console.error('Error:', error));
    });
}

function initializeSalidaAlmacen() {
    const form = document.getElementById('salida-almacen-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {
            items: [{
                item_id: formData.get('item_id'),
                cantidad: parseInt(formData.get('cantidad'))
            }]
        };
        fetch('/inventario/api/salida-almacen', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            alert(result.message);
            form.reset();
            initializeInventarioActual();
        })
        .catch(error => console.error('Error:', error));
    });
}

function initializeInventarioActual() {
    fetch('/inventario/api/inventario')
        .then(response => response.json())
        .then(items => {
            const tableBody = document.querySelector('#inventario-actual-table tbody');
            tableBody.innerHTML = '';
            items.forEach(item => {
                const row = `
                    <tr>
                        <td>${item.codigo}</td>
                        <td>${item.nombre}</td>
                        <td>${item.categoria}</td>
                        <td>${item.stock}</td>
                        <td>${item.precio}</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => console.error('Error:', error));
}

function initializeReporteInventario() {
    const form = document.getElementById('reporte-inventario-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        const queryParams = new URLSearchParams({
            fecha_inicio: formData.get('fecha_inicio'),
            fecha_fin: formData.get('fecha_fin')
        }).toString();
        fetch(`/inventario/api/reporte?${queryParams}`)
            .then(response => response.json())
            .then(data => {
                const tableBody = document.querySelector('#reporte-inventario-table tbody');
                tableBody.innerHTML = '';
                data.forEach(item => {
                    const row = `
                        <tr>
                            <td>${item.item.codigo}</td>
                            <td>${item.item.nombre}</td>
                            <td>${item.entradas}</td>
                            <td>${item.salidas}</td>
                            <td>${item.item.stock}</td>
                        </tr>
                    `;
                    tableBody.innerHTML += row;
                });
            })
            .catch(error => console.error('Error:', error));
    });
}

function editItem(itemId) {
    // Implementar lógica para editar un item
    console.log('Editar item:', itemId);
}

function deleteItem(itemId) {
    if (confirm('¿Estás seguro de que quieres eliminar este item?')) {
        fetch(`/inventario/api/items/${itemId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (response.ok) {
                alert('Item eliminado correctamente');
                initializeItemsTable();
            } else {
                throw new Error('Error al eliminar el item');
            }
        })
        .catch(error => console.error('Error:', error));
    }
}