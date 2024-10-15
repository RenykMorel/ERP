// Inicialización unificada
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
    loadModules();
    loadTasks();
    loadNotifications();
    initializeCharts();
    initializeCalendar();
    initializeAsistente();
    initializeSubmoduleHandlers();
    initializeAuthForms();
    initializeMarketingModule();
    initializeRRHHModule();
    initializeComprasModule();
    initializeActivosFijosModule();
    initializeCuentasPorPagarModule();
    initializeImportacionModule();
    initializeProyectosModule();
    initializeCuentasPorCobrarModule();
    window.addEventListener('resize', resizeCharts);

    ['line', 'bar', 'pie'].forEach(type => {
        const toggleButton = document.getElementById(`toggle-${type}-chart`);
        if (toggleButton) {
            toggleButton.addEventListener('click', () => toggleChartVisibility(`${type}-chart`));
        }
    });
});

// Función para notificar al asistente virtual
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

// Función para mostrar mensajes con archivos descargables
function mostrarMensajeConArchivos(mensaje, archivos) {
    const mensajesDiv = document.getElementById('asistente-mensajes');
    if (mensajesDiv) {
        const mensajeDiv = document.createElement('div');
        mensajeDiv.className = 'assistant-message';
        mensajeDiv.innerHTML = `<p>${mensaje}</p>`;
        
        Object.entries(archivos).forEach(([formato, contenido]) => {
            const enlace = document.createElement('a');
            enlace.href = `data:application/${formato === 'excel' ? 'vnd.openxmlformats-officedocument.spreadsheetml.sheet' : formato};base64,${contenido}`;
            enlace.download = `modulos.${formato === 'excel' ? 'xlsx' : formato}`;
            enlace.textContent = `Descargar ${formato.toUpperCase()}`;
            enlace.className = 'archivo-descargable';
            mensajeDiv.appendChild(enlace);
            mensajeDiv.appendChild(document.createElement('br'));
        });
        
        mensajesDiv.appendChild(mensajeDiv);
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }
}

// Función para descargar un archivo
function descargarArchivo(contenido, nombre, mimetype) {
    const blob = b64toBlob(contenido, mimetype);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombre;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Función para convertir base64 a Blob
function b64toBlob(b64Data, contentType = '', sliceSize = 512) {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        const slice = byteCharacters.slice(offset, offset + sliceSize);
        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }

    const blob = new Blob(byteArrays, {type: contentType});
    return blob;
}

// Función para mostrar archivos descargables
function mostrarArchivosDescargables(archivos) {
    const mensajesDiv = document.getElementById('asistente-mensajes');
    if (mensajesDiv) {
        const archivosMensaje = document.createElement('div');
        archivosMensaje.innerHTML = '<p>Aquí tienes los archivos solicitados:</p>';
        
        Object.entries(archivos).forEach(([formato, archivo]) => {
            const enlace = document.createElement('a');
            enlace.href = `data:${archivo.mimetype};base64,${archivo.contenido}`;
            enlace.download = archivo.nombre;
            enlace.textContent = `Descargar ${formato.toUpperCase()}`;
            enlace.className = 'archivo-descargable';
            archivosMensaje.appendChild(enlace);
        });
        
        mensajesDiv.appendChild(archivosMensaje);
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }
}

// Función para mostrar mensajes del asistente
function handleAsistenteResponse(response) {
    console.log("Respuesta recibida:", response);  // Para depuración

    if (response.tipo === 'reporte') {
        mostrarVentanaReporte(response.datos, response.tipo_reporte);
        mostrarMensajeAsistente(response.mensaje);
    } else if (response.tipo === 'texto') {
        mostrarMensajeAsistente(response.respuesta);
    } else {
        console.error("Tipo de respuesta desconocido:", response.tipo);
        mostrarMensajeAsistente("Lo siento, ha ocurrido un error al procesar la respuesta.");
    }
}

function mostrarMensajeAsistente(mensaje) {
    const mensajesDiv = document.getElementById('asistente-mensajes');
    const nuevoMensaje = document.createElement('p');
    nuevoMensaje.textContent = mensaje;
    mensajesDiv.appendChild(nuevoMensaje);
    mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
}

function mostrarVentanaReporte(datos, tipoReporte) {
    const ventanaReporte = document.createElement('div');
    ventanaReporte.className = 'ventana-reporte';
    
    const titulo = document.createElement('h2');
    titulo.textContent = `Reporte: ${tipoReporte}`;
    ventanaReporte.appendChild(titulo);

    const tabla = crearTablaDesdeVatos(datos);
    ventanaReporte.appendChild(tabla);

    const botonDescargar = document.createElement('button');
    botonDescargar.textContent = 'Descargar Reporte';
    botonDescargar.onclick = () => descargarReporte(datos, tipoReporte);
    ventanaReporte.appendChild(botonDescargar);

    const botonCerrar = document.createElement('button');
    botonCerrar.textContent = 'Cerrar';
    botonCerrar.onclick = () => document.body.removeChild(ventanaReporte);
    ventanaReporte.appendChild(botonCerrar);

    document.body.appendChild(ventanaReporte);
}

function crearTablaDesdeVatos(datos) {
    const tabla = document.createElement('table');
    datos.forEach((fila, index) => {
        const tr = document.createElement('tr');
        fila.forEach(celda => {
            const td = document.createElement(index === 0 ? 'th' : 'td');
            td.textContent = celda;
            tr.appendChild(td);
        });
        tabla.appendChild(tr);
    });
    return tabla;
}

function descargarReporte(datos, tipoReporte) {
    let contenidoCsv = datos.map(fila => fila.join(',')).join('\n');
    let blob = new Blob([contenidoCsv], { type: 'text/csv;charset=utf-8;' });
    let url = URL.createObjectURL(blob);
    let link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `reporte_${tipoReporte.replace(/\s+/g, '_')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Función genérica para manejar formularios de autenticación
function handleAuthForm(event, endpoint) {
    event.preventDefault();
    const formData = new FormData(event.target);
    fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/';  // Redirige al home en caso de éxito
        } else {
            if (data.allow_password_reset) {
                showPasswordResetOption(data.username);
            } else {
                showError(data.error);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Ocurrió un error en el proceso de autenticación');
    });
}

function showPasswordResetOption(username) {
    const authContainer = document.querySelector('.auth-container');
    authContainer.innerHTML = `
        <h2>Cambiar Contraseña</h2>
        <form id="form-reset-password">
            <input type="hidden" name="username" value="${username}">
            <input type="password" name="new_password" placeholder="Nueva contraseña" required>
            <input type="password" name="confirm_password" placeholder="Confirmar nueva contraseña" required>
            <button type="submit">Cambiar Contraseña</button>
        </form>
        <p>¿Olvidaste tu contraseña? <a href="#" id="forgot-password">Haz clic aquí</a></p>
    `;
    document.getElementById('form-reset-password').addEventListener('submit', handlePasswordReset);
    document.getElementById('forgot-password').addEventListener('click', showForgotPasswordForm);
}

function handlePasswordReset(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    if (formData.get('new_password') !== formData.get('confirm_password')) {
        showError('Las contraseñas no coinciden');
        return;
    }
    fetch('/reset_password', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Contraseña cambiada exitosamente. Por favor, inicia sesión con tu nueva contraseña.');
            window.location.href = '/login';
        } else {
            showError(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Ocurrió un error al cambiar la contraseña');
    });
}

function showForgotPasswordForm() {
    const authContainer = document.querySelector('.auth-container');
    authContainer.innerHTML = `
        <h2>Restablecer Contraseña</h2>
        <form id="form-forgot-password">
            <input type="email" name="email" placeholder="Correo electrónico" required>
            <button type="submit">Enviar Instrucciones</button>
        </form>
    `;
    document.getElementById('form-forgot-password').addEventListener('submit', handleForgotPassword);
}

function handleForgotPassword(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    fetch('/request_password_reset', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            window.location.href = '/login';
        } else {
            showError(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Ocurrió un error al solicitar el restablecimiento de contraseña');
    });
}

function showError(message) {
    const errorDiv = document.getElementById('auth-error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    } else {
        alert(message);
    }
}

function initializeAuthForms() {
    const formLogin = document.getElementById('form-login');
    const formRegistro = document.getElementById('form-registro');

    if (formLogin) {
        formLogin.addEventListener('submit', (e) => handleAuthForm(e, '/login'));
    }

    if (formRegistro) {
        formRegistro.addEventListener('submit', (e) => handleAuthForm(e, '/registro'));
    }
}

// Inicializa los manejadores de submódulos
function initializeSubmoduleHandlers() {
    document.querySelectorAll('.submodule-button').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const moduleName = this.closest('.module-wrapper').querySelector('.rectangular-button').textContent;
            const submoduleName = this.textContent;
            handleSubmoduleClick(moduleName, submoduleName);
        });
    });

    // Añade este nuevo bloque para manejar los enlaces de contabilidad
    const contabilidadLinks = document.querySelectorAll('#sidebar a[href^="/contabilidad/"]');
    contabilidadLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('href');
            cargarContenido(url);
        });
    });
}

// Maneja el clic en submódulos
function handleSubmoduleClick(moduleName, submoduleName) {
    console.log(`Clicked on ${submoduleName} of ${moduleName}`);
    if (moduleName === 'Facturacion') {
        switch (submoduleName) {
            case 'Facturas':
                window.location.href = '/facturacion/facturas';
                break;
            case 'Pre-facturas':
                window.location.href = '/facturacion/pre-facturas';
                break;
            case 'Notas de Crédito/Débito':
                window.location.href = '/facturacion/notas-de-credito-debito';
                break;
            case 'Reporte de Ventas':
                window.location.href = '/facturacion/reporte-de-ventas';
                break;
            case 'Gestión de Clientes':
                window.location.href = '/facturacion/gestion-de-clientes';
                break;
            default:
                console.log('Submódulo de Facturación no reconocido');
        }
    } else if (moduleName === 'Cuentas Por Pagar') {
        switch (submoduleName) {
            case 'Factura Suplidor':
                window.location.href = '/cxp/factura-suplidor';
                break;
            case 'Nota de Crédito':
                window.location.href = '/cxp/nota-credito';
                break;
            case 'Nota de Débito':
                window.location.href = '/cxp/nota-debito';
                break;
            case 'Orden de Compras':
                window.location.href = '/cxp/orden-compras';
                break;
            case 'Suplidor':
                window.location.href = '/cxp/suplidor';
                break;
            case 'Anticipo CxP':
                window.location.href = '/cxp/anticipo-cxp';
                break;
            case 'Pago de Contado':
                window.location.href = '/cxp/pago-contado';
                break;
            case 'Reporte CxP':
                window.location.href = '/cxp/reporte-cxp';
                break;
            case 'Requisición Cotización':
                window.location.href = '/cxp/requisicion-cotizacion';
                break;
            case 'Solicitud Compras':
                window.location.href = '/cxp/solicitud-compras';
                break;
            case 'Tipo de Suplidor':
                window.location.href = '/cxp/tipo-suplidor';
                break;
            default:
                console.log('Submódulo de Cuentas Por Pagar no reconocido');
        }    
    } else if (moduleName === 'Activos Fijos') {
        switch (submoduleName) {
            case 'Activo Fijo':
                window.location.href = '/activos_fijos/activo_fijo';
                break;
            case 'Depreciación':
                window.location.href = '/activos_fijos/depreciacion';
                break;
            case 'Retiro':
                window.location.href = '/activos_fijos/retiro';
                break;
            case 'Revalorización':
                window.location.href = '/activos_fijos/revalorizacion';
                break;
            case 'Tipo de Activo Fijo':
                window.location.href = '/activos_fijos/tipo_activo_fijo';
                break;
            default:
                console.log('Submódulo de Activos Fijos no reconocido');
        }
    } else if (moduleName === 'Importacion') {
        switch (submoduleName) {
            case 'Expediente de Importacion':
                window.location.href = '/importacion/expediente';
                break;
            case 'Importador':
                window.location.href = '/importacion/importador';
                break;
            case 'Reportes Importacion':
                window.location.href = '/importacion/reportes';
                break;
            default:
                console.log('Submódulo de Importación no reconocido');
        }
    } else if (moduleName === 'Cuentas Por Cobrar') {
        switch (submoduleName) {
            case 'Cliente':
                window.location.href = '/cxc/clientes';
                break;
            case 'Descuento y devoluciones':
                window.location.href = '/cxc/descuentos-devoluciones';
                break;
            case 'Nota de credito':
                window.location.href = '/cxc/notas-credito';
                break;
            case 'Nota de debito':
                window.location.href = '/cxc/notas-debito';
                break;
            case 'Recibo':
                window.location.href = '/cxc/recibos';
                break;
            case 'Anticipo CxC':
                window.location.href = '/cxc/anticipos';
                break;
            case 'Condicion de pago':
                window.location.href = '/cxc/condiciones-pago';
                break;
            case 'Reporte CxC':
                window.location.href = '/cxc/reporte';
                break;
            case 'Tipo de cliente':
                window.location.href = '/cxc/tipos-cliente';
                break;
            default:
                console.log('Submódulo de Cuentas Por Cobrar no reconocido');
        }
    } else if (moduleName === 'Impuestos') {
        switch (submoduleName) {
            case 'Formulario 606':
                window.location.href = '/impuestos/formulario606';
                break;
            case 'Formulario 607':
                window.location.href = '/impuestos/formulario607';
                break;
            case 'Reporte IT1':
                window.location.href = '/impuestos/reporte-it1';
                break;
            case 'Impuesto sobre la Renta (IR17)':
                window.location.href = '/impuestos/ir17';
                break;
            case 'Serie Fiscal':
                window.location.href = '/impuestos/serie-fiscal';
                break;
            case 'Configuraciones':
                window.location.href = '/impuestos/configuraciones';
                break;
            default:
                console.log('Submódulo de Impuestos no reconocido');
        }
    } else if (moduleName === 'Banco') {
        switch (submoduleName) {
            case 'Bancos':
                window.location.href = '/Bancos';
                break;
            case 'Depósitos':
                window.location.href = '/depositos';
                break;
            case 'Notas de Crédito/Débito':
                window.location.href = '/notas-credito-debito';
                break;
            case 'Transferencias Bancarias':
                window.location.href = '/transferencias-bancarias';
                break;
            case 'Conciliación Bancaria':
                window.location.href = '/conciliacion-bancaria';
                break;
            case 'Gestión de Bancos':
                window.location.href = '/gestion-bancos';
                break;
            case 'Divisas':
                window.location.href = '/divisas';
                break;
            default:
                console.log('Submódulo de Banco no reconocido');
        }
    } else if (moduleName === 'Compras') {
        switch (submoduleName) {
            case 'Solicitudes de Compra':
                window.location.href = '/compras/solicitudes';
                break;
            case 'Órdenes de Compra':
                window.location.href = '/compras/ordenes';
                break;
            case 'Recepción de Materiales':
                window.location.href = '/compras/recepcion';
                break;
            case 'Gastos':
                window.location.href = '/compras/gastos';
                break;
            case 'Reporte de Compras/Gastos':
                window.location.href = '/compras/reporte';
                break;
            default:
                console.log('Submódulo de Compras no reconocido');
        }
    } else if (moduleName === 'Contabilidad') {
        switch (submoduleName) {
            case 'Cuentas':
                window.location.href = '/contabilidad/cuentas';
                break;
            case 'Diario':
                window.location.href = '/contabilidad/diario';
                break;
            case 'Mayor General':
                window.location.href = '/contabilidad/mayor_general';
                break;
            case 'Balanza de Comprobación':
                window.location.href = '/contabilidad/balanza_comprobacion';
                break;
            case 'Estado de Resultados':
                window.location.href = '/contabilidad/estado_resultados';
                break;
            case 'Balance General':
                window.location.href = '/contabilidad/balance_general';
                break;
            case 'Configuraciones':
                window.location.href = '/contabilidad/configuraciones';
                break;
            case 'Flujo de caja':
                window.location.href = '/contabilidad/flujo_caja';
                break;
            default:
                console.log('Submódulo de Contabilidad no reconocido');
        }
    } else if (moduleName === 'Recursos Humanos') {
        switch (submoduleName) {
            case 'Gestión de Empleados':
                window.location.href = '/rrhh/empleados';
                break;
            case 'Nómina':
                window.location.href = '/rrhh/nomina';
                break;
            case 'Evaluación de Desempeño':
                window.location.href = '/rrhh/evaluacion';
                break;
            default:
                console.log('Submódulo de Recursos Humanos no reconocido');
        }
    } else if (moduleName === 'Proyectos') {
        switch (submoduleName) {
            case 'Gestión de Proyectos':
                window.location.href = '/proyectos/gestion';
                break;
            case 'Presupuestos':
                window.location.href = '/proyectos/presupuestos';
                break;
            case 'Facturación por Proyecto':
                window.location.href = '/proyectos/facturacion';
                break;
            default:
                console.log('Submódulo de Proyectos no reconocido');
        }
    } else if (moduleName === 'Inventario') {
        switch (submoduleName) {
            case 'Items':
                window.location.href = '/inventario/items';
                break;
            case 'Entrada de Almacén':
                window.location.href = '/inventario/entrada-almacen';
                break;
            case 'Salida de Almacén':
                window.location.href = '/inventario/salida-almacen';
                break;
            case 'Inventario':
                window.location.href = '/inventario/inventario';
                break;
            case 'Reporte de Inventario':
                window.location.href = '/inventario/reporte';
                break;
            default:
                console.log('Submódulo de Inventario no reconocido');
        }
    } else if (moduleName === 'Marketing') {
        switch (submoduleName) {
            case 'Gestión de Contactos':
                window.location.href = '/marketing/contacts';
                break;
            case 'Campañas de Email':
                window.location.href = '/marketing/campaigns';
                break;
            case 'Plantillas de Email':
                window.location.href = '/marketing/templates';
                break;
            case 'Reportes de Campañas':
                window.location.href = '/marketing/reports';
                break;
            case 'Segmentación de Contactos':
                window.location.href = '/marketing/segmentation';
                break;
            case 'Automatizaciones':
                window.location.href = '/marketing/automations';
                break;
            case 'Integración de Redes Sociales':
                window.location.href = '/marketing/social-media';
                break;
            default:
                console.log('Submódulo de Marketing no reconocido');
        }
    } else {
        console.log('Otro submódulo clickeado');
        loadSubmoduleContent(moduleName, submoduleName);
    }
}

// Carga la información del usuario desde la API
function loadUserInfo() {
    fetch('/api/usuario')
        .then(response => response.json())
        .then(usuario => {
            document.getElementById('user-name').textContent = usuario.nombre;
            document.getElementById('user-id').textContent = usuario.id;
        })
        .catch(error => console.error('Error loading user info:', error));
}

// Carga los módulos del sistema desde la API
function loadModules() {
    fetch('/api/modulos')
        .then(response => response.json())
        .then(modulos => {
            const moduleContainer = document.getElementById('module-container');
            moduleContainer.innerHTML = '';
            const modulosConfig = [
                { nombre: "Banco", color: "#FF6B6B", icon: "fas fa-university" },
                { nombre: "Contabilidad", color: "#4ECDC4", icon: "fas fa-calculator" },
                { nombre: "Activos Fijos", color: "#45B7D1", icon: "fas fa-building" },
                { nombre: "Cuentas Por Cobrar", color: "#FFA07A", icon: "fas fa-file-invoice-dollar" },
                { nombre: "Cuentas Por Pagar", color: "#FFC0CB", icon: "fas fa-file-invoice" },
                { nombre: "Facturacion", color: "#98D8C8", icon: "fas fa-file-alt" },
                { nombre: "Impuestos", color: "#F06292", icon: "fas fa-percentage" },
                { nombre: "Inventario", color: "#AED581", icon: "fas fa-boxes" },
                { nombre: "Compras", color: "#FFD54F", icon: "fas fa-shopping-cart" },
                { nombre: "Importacion", color: "#800000", icon: "fas fa-ship" },
                { nombre: "Proyectos", color: "#4DB6AC", icon: "fas fa-project-diagram" },
                { nombre: "Recursos Humanos", color: "#075e56", icon: "fas fa-users" },
                { nombre: "Marketing", color: "#9C27B0", icon: "fas fa-bullhorn" }
            ];
            
            modulosConfig.forEach(config => {
                if (modulos.includes(config.nombre)) {
                    const moduleDiv = createModuleElement(config.nombre, config.color, config.icon);
                    moduleContainer.appendChild(moduleDiv);
                }
            });
            if (isAdmin()) {
                const adminPanel = createModuleElement("Panel de Administración", "#3498db", "fas fa-cogs");
                adminPanel.querySelector('button').onclick = () => window.location.href = '/admin_panel';
                moduleContainer.appendChild(adminPanel);
            }

            // Agregar botón de Cerrar Sesión
            const logoutButton = createModuleElement("Cerrar Sesión", "#e74c3c", "fas fa-sign-out-alt");
            logoutButton.querySelector('button').onclick = handleLogout;
            moduleContainer.appendChild(logoutButton);
        })
        .catch(error => console.error('Error loading modules:', error));
}

// Crea un elemento HTML para un módulo
function createModuleElement(modulo, color, icon) {
    const moduleDiv = document.createElement('div');
    moduleDiv.className = 'module-wrapper';
    
    const button = createButton(modulo, 'rectangular-button', color, icon);
    if (modulo !== "Panel de Administración" && modulo !== "Cerrar Sesión") {
        button.onclick = () => toggleSubmodules(modulo, moduleDiv);
    }
    
    const submoduleContainer = document.createElement('div');
    submoduleContainer.className = 'submodule-container';
    
    moduleDiv.appendChild(button);
    moduleDiv.appendChild(submoduleContainer);
    return moduleDiv;
}

// Crea un botón genérico
function createButton(text, className, color, icon) {
    const button = document.createElement('button');
    button.className = className;
    if (color) button.style.backgroundColor = color;
    
    if (icon) {
        const iconElement = document.createElement('i');
        iconElement.className = icon;
        iconElement.style.marginRight = '10px';
        button.appendChild(iconElement);
    }
    
    const textSpan = document.createElement('span');
    textSpan.textContent = text;
    button.appendChild(textSpan);
    
    return button;
}

// Alterna la visibilidad de los submódulos
function toggleSubmodules(moduleName, moduleDiv) {
    const submoduleContainer = moduleDiv.querySelector('.submodule-container');
    const moduleButton = moduleDiv.querySelector('.rectangular-button');

    // Cerrar todos los otros contenedores de submódulos
    document.querySelectorAll('.submodule-container').forEach(container => {
        if (container !== submoduleContainer) {
            container.style.display = 'none';
        }
    });

    // Quitar la clase 'active' de todos los otros botones de módulo
    document.querySelectorAll('.rectangular-button').forEach(btn => {
        if (btn !== moduleButton) {
            btn.classList.remove('active');
        }
    });

    // Alternar la visibilidad del contenedor de submódulos actual
    if (submoduleContainer.style.display === 'none' || submoduleContainer.style.display === '') {
        moduleButton.classList.add('active');
        submoduleContainer.style.display = 'block';
        loadSubmodules(moduleName, submoduleContainer);
    } else {
        moduleButton.classList.remove('active');
        submoduleContainer.style.display = 'none';
    }
}

// Carga los submódulos de un módulo específico
function loadSubmodules(moduleName, submoduleContainer) {
    if (submoduleContainer.children.length === 0) {
        fetch(`/api/submodulos/${moduleName}`)
            .then(response => response.json())
            .then(submodulos => {
                submoduleContainer.innerHTML = '';
                submodulos.forEach(submodulo => {
                    const button = createButton(submodulo, 'submodule-button', null, 'fas fa-circle');
                    button.onclick = (event) => {
                        event.preventDefault();
                        handleSubmoduleClick(moduleName, submodulo);
                    };
                    submoduleContainer.appendChild(button);
                });
                // Mostrar el contenedor de submódulos
                submoduleContainer.style.display = 'flex';
                submoduleContainer.style.flexDirection = 'column';
                submoduleContainer.style.alignItems = 'center';
            })
            .catch(error => console.error('Error loading submodules:', error));
    }
}

function loadSubmoduleContent(moduleName, submoduleName) {
    console.log(`Loading content for ${moduleName} - ${submoduleName}`);
    
    let url = `/api/submodule-content/${moduleName}/${submoduleName}`;
    
    console.log('Fetching from URL:', url);

    fetch(url, {
        method: 'GET',
        headers: {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', [...response.headers.entries()]);
        
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
            });
        }
        return response.text();
    })
    .then(htmlContent => {
        console.log("Contenido recibido (primeros 100 caracteres):", htmlContent.substring(0, 100));
        
        let contentContainer = document.getElementById('contenido-principal');
        if (!contentContainer) {
            console.log('Creando nuevo contenedor de contenido');
            contentContainer = document.createElement('div');
            contentContainer.id = 'contenido-principal';
            document.body.appendChild(contentContainer);
        }
        
        contentContainer.innerHTML = htmlContent;
    })
    .catch(error => {
        console.error('Error loading submodule content:', error);
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        
        let contentContainer = document.getElementById('contenido-principal');
        if (!contentContainer) {
            contentContainer = document.createElement('div');
            contentContainer.id = 'contenido-principal';
            document.body.appendChild(contentContainer);
        }
        
        contentContainer.innerHTML = `
            <p>Error al cargar el contenido:</p>
            <pre>${error.name}: ${error.message}</pre>
            <p>Por favor, revise la consola para más detalles y contacte al soporte técnico si el problema persiste.</p>
        `;
    });
}

// Carga las notificaciones desde la API
function loadNotifications() {
    fetch('/api/notificaciones')
        .then(response => response.json())
        .then(notificaciones => {
            const notificationList = document.getElementById('notification-list');
            notificationList.innerHTML = notificaciones.map(notificacion => 
                `<li class="${notificacion.tipo}">${notificacion.mensaje}</li>`
            ).join('');
        })
        .catch(error => console.error('Error loading notifications:', error));
}

// Opciones comunes para los gráficos
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Título del Gráfico' }
    },
    scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: 'rgba(0, 0, 0, 0.1)' } }
    }
};

// Variables globales para los gráficos
let lineChart, barChart, pieChart;

// Inicializa los gráficos
function initializeCharts() {
    fetch('/api/datos_graficos')
        .then(response => response.json())
        .then(datos => {
            createLineChart(datos.ventas);
            createBarChart(datos.ingresos_vs_gastos);
            createPieChart(datos.distribucion);
        })
        .catch(error => console.error('Error initializing charts:', error));
}

// Crea el gráfico de líneas
function createLineChart(data) {
    const ctx = document.getElementById('line-chart').getContext('2d');
    lineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Ventas',
                data: data.values,
                borderColor: '#FF6B6B',
                backgroundColor: 'rgba(255, 107, 107, 0.2)'
            }]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: { display: true, text: 'Ventas' }
            }
        }
    });
}

// Crea el gráfico de barras
function createBarChart(data) {
    const ctx = document.getElementById('bar-chart').getContext('2d');
    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Ingresos',
                data: data.ingresos,
                backgroundColor: '#4ECDC4'
            }, {
                label: 'Gastos',
                data: data.gastos,
                backgroundColor: '#FF6B6B'
            }]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: { display: true, text: 'Ingresos vs Gastos' }
            }
        }
    });
}

// Crea el gráfico circular (pie)
function createPieChart(data) {
    const ctx = document.getElementById('pie-chart').getContext('2d');
    pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: ['#FF6B6B', '#4ECDC4', '#FFA07A', '#FFC0CB']
            }]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: { display: true, text: 'Distribución' }
            }
        }
    });
}

// Ajusta los gráficos al redimensionar la ventana
function resizeCharts() {
    if (lineChart) lineChart.resize();
    if (barChart) barChart.resize();
    if (pieChart) pieChart.resize();
}

// Alterna la visibilidad de los gráficos
function toggleChartVisibility(chartId) {
    const chartContainer = document.getElementById(chartId);
    chartContainer.style.display = chartContainer.style.display === 'none' ? 'block' : 'none';
}

// Inicializa el calendario
function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: '/api/eventos',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        }
    });

    calendarEl.style.width = '60%';
    calendarEl.style.maxWidth = '600px';
    calendarEl.style.height = '400px';
    calendarEl.style.borderRadius = '8px';
    calendarEl.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';

    calendar.render();
}

// Inicializa el asistente virtual
function initializeAsistente() {
    const chatWindow = document.getElementById('chat-window');
    const chatMessages = document.getElementById('chat-messages');
    const asistenteInput = document.getElementById('assistant-input');
    const asistenteEnviar = document.getElementById('assistant-send');

    let conversationHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
    let asistenteActivo = false;
    let messageCount = 0;

    // Función para cargar el historial de conversación
    function cargarHistorialConversacion() {
        chatMessages.innerHTML = ''; // Limpia los mensajes existentes
        conversationHistory.forEach(entry => {
            const mensajeElement = document.createElement('p');
            mensajeElement.className = entry.sender === 'Usuario' ? 'user-message' : 'assistant-message';
            mensajeElement.textContent = `${entry.sender}: ${entry.message}`;
            chatMessages.appendChild(mensajeElement);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Comprobar si el asistente está activo
    fetch('/api/asistente_status')
        .then(response => response.json())
        .then(data => {
            console.log('Estado del asistente:', data);
            asistenteActivo = data.activo;
            if (asistenteActivo && conversationHistory.length === 0) {
                const lastWelcomeDate = localStorage.getItem('lastWelcomeDate');
                const today = new Date().toDateString();
                if (lastWelcomeDate !== today) {
                    const mensajeBienvenida = "¡Hola! Soy tu asistente virtual de CalculAI. ¿En qué puedo ayudarte hoy?";
                    conversationHistory.push({ sender: 'Asistente', message: mensajeBienvenida });
                    localStorage.setItem('chatHistory', JSON.stringify(conversationHistory));
                    localStorage.setItem('lastWelcomeDate', today);
                }
            }
            cargarHistorialConversacion();
        })
        .catch(error => {
            console.error('Error al verificar el estado del asistente:', error);
            chatWindow.classList.add('asistente-inactivo');
            mostrarMensajeAsistente("Error al verificar el estado del asistente. Por favor, intente más tarde.");
        });

    if (asistenteInput && asistenteEnviar) {
        asistenteEnviar.addEventListener('click', enviarMensaje);
        asistenteInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                enviarMensaje();
            }
        });
    }

    function enviarMensaje() {
        const pregunta = asistenteInput.value.trim();
        if (pregunta) {
            mostrarMensajeUsuario(pregunta);
            notificarAsistente(pregunta);
            asistenteInput.value = '';
            messageCount++;

            if (messageCount % 10 === 0) {
                preguntarLimpiarChat();
            }
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

    function preguntarLimpiarChat() {
        const confirmacion = confirm("¿Deseas limpiar el historial del chat?");
        if (confirmacion) {
            limpiarChat();
        }
    }

    function limpiarChat() {
        conversationHistory = [];
        localStorage.setItem('chatHistory', JSON.stringify(conversationHistory));
        chatMessages.innerHTML = '';
        messageCount = 0;
    }

    // Exponer la función mostrarMensajeAsistente para uso externo
    window.mostrarMensajeAsistente = mostrarMensajeAsistente;
}

function mostrarMensajeUsuario(mensaje) {
    const mensajesDiv = document.getElementById('asistente-mensajes');
    if (mensajesDiv) {
        const nuevoMensaje = document.createElement('p');
        nuevoMensaje.textContent = `Tú: ${mensaje}`;
        nuevoMensaje.className = 'mensaje-usuario';
        mensajesDiv.appendChild(nuevoMensaje);
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }
}

// Función para verificar si el usuario es administrador
function isAdmin() {
    // Esta función debería implementarse según la lógica de tu aplicación
    // Por ejemplo, podrías verificar una variable global o hacer una petición al servidor
    return false; // Placeholder
}

// Función para manejar el cierre de sesión
function handleLogout() {
    fetch('/logout', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/login';
            } else {
                console.error('Error durante el cierre de sesión:', data.error);
            }
        })
        .catch(error => console.error('Error durante el cierre de sesión:', error));
}

// Carga las tareas desde la API
function loadTasks() {
    fetch('/api/tareas')
        .then(response => response.json())
        .then(tareas => {
            const taskList = document.getElementById('task-list');
            taskList.innerHTML = tareas.map(tarea => 
                `<li>${tarea.descripcion} - Vence: ${tarea.vence}</li>`
            ).join('');
        })
        .catch(error => console.error('Error loading tasks:', error));
}

// Inicializa el módulo de Marketing
function initializeMarketingModule() {
    const marketingContainer = document.getElementById('marketing-container');
    if (marketingContainer) {
        loadContacts();
        loadCampaigns();
        initializeContactForm();
        initializeCampaignForm();
    }
}

// Carga los contactos desde la API
function loadContacts() {
    fetch('/marketing/api/contacts')
        .then(response => response.json())
        .then(contacts => {
            const contactList = document.getElementById('contact-list');
            if (contactList) {
                contactList.innerHTML = contacts.map(contact => 
                    `<li>${contact.name} - ${contact.email} - ${contact.company || 'N/A'}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading contacts:', error));
}

// Carga las campañas desde la API
function loadCampaigns() {
    fetch('/marketing/api/campaigns')
        .then(response => response.json())
        .then(campaigns => {
            const campaignList = document.getElementById('campaign-list');
            if (campaignList) {
                campaignList.innerHTML = campaigns.map(campaign => 
                    `<li>${campaign.name} - ${campaign.subject} 
                    ${campaign.sent_at ? `Enviado: ${campaign.sent_at}` : 
                    `<button onclick="sendCampaign(${campaign.id})">Enviar</button>`}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading campaigns:', error));
}

// Inicializa el formulario de contactos
function initializeContactForm() {
    const contactForm = document.getElementById('add-contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(contactForm);
            fetch('/marketing/api/contacts', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Contact added:', data);
                loadContacts();
                contactForm.reset();
            })
            .catch(error => console.error('Error adding contact:', error));
        });
    }
}

// Inicializa el formulario de campañas
function initializeCampaignForm() {
    const campaignForm = document.getElementById('create-campaign-form');
    if (campaignForm) {
        campaignForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(campaignForm);
            fetch('/marketing/api/campaigns', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Campaign created:', data);
                loadCampaigns();
                campaignForm.reset();
            })
            .catch(error => console.error('Error creating campaign:', error));
        });
    }
}

// Función para enviar una campaña
function sendCampaign(campaignId) {
    fetch(`/marketing/api/send_campaign/${campaignId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Campaign sent:', data);
        loadCampaigns();
    })
    .catch(error => console.error('Error sending campaign:', error));
}

// Función para cargar las métricas de una campaña
function loadCampaignMetrics(campaignId) {
    fetch(`/marketing/api/campaign_metrics/${campaignId}`)
        .then(response => response.json())
        .then(metrics => {
            console.log('Campaign metrics:', metrics);
            // Aquí puedes actualizar la UI con las métricas
        })
        .catch(error => console.error('Error loading campaign metrics:', error));
}

// Función para inicializar el editor de plantillas de email
function initializeEmailTemplateEditor() {
    // Aquí puedes implementar la lógica para el editor de plantillas
    // Por ejemplo, podrías usar una librería como Quill o TinyMCE
}

// Función para cargar la segmentación de contactos
function loadContactSegmentation() {
    // Implementa la lógica para cargar y mostrar los segmentos de contactos
}

// Función para inicializar las automatizaciones de marketing
function initializeMarketingAutomations() {
    // Implementa la lógica para configurar y mostrar las automatizaciones
}

// Función para integrar redes sociales
function initializeSocialMediaIntegration() {
    // Implementa la lógica para conectar y mostrar las integraciones de redes sociales
}

// Funciones específicas para el módulo de RRHH
function initializeRRHHModule() {
    const rrhhContainer = document.getElementById('rrhh-container');
    if (rrhhContainer) {
        loadEmpleados();
        loadNominas();
        loadEvaluaciones();
        initializeEmpleadoForm();
        initializeNominaForm();
        initializeEvaluacionForm();
    }
}

function loadEmpleados() {
    fetch('/rrhh/api/empleados')
        .then(response => response.json())
        .then(empleados => {
            const empleadosList = document.getElementById('empleados-list');
            if (empleadosList) {
                empleadosList.innerHTML = empleados.map(empleado => 
                    `<li>${empleado.nombre} ${empleado.apellido} - ${empleado.puesto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading empleados:', error));
}

function loadNominas() {
    fetch('/rrhh/api/nominas')
        .then(response => response.json())
        .then(nominas => {
            const nominasList = document.getElementById('nominas-list');
            if (nominasList) {
                nominasList.innerHTML = nominas.map(nomina => 
                    `<li>${nomina.empleado} - ${nomina.fecha} - $${nomina.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading nóminas:', error));
}

function loadEvaluaciones() {
    fetch('/rrhh/api/evaluaciones')
        .then(response => response.json())
        .then(evaluaciones => {
            const evaluacionesList = document.getElementById('evaluaciones-list');
            if (evaluacionesList) {
                evaluacionesList.innerHTML = evaluaciones.map(evaluacion => 
                    `<li>${evaluacion.empleado} - ${evaluacion.fecha} - Puntuación: ${evaluacion.puntuacion}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading evaluaciones:', error));
}

function initializeEmpleadoForm() {
    const empleadoForm = document.getElementById('empleado-form');
    if (empleadoForm) {
        empleadoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(empleadoForm);
            fetch('/rrhh/api/empleados', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Empleado creado:', data);
                loadEmpleados();
                empleadoForm.reset();
            })
            .catch(error => console.error('Error creando empleado:', error));
        });
    }
}

function initializeNominaForm() {
    const nominaForm = document.getElementById('nomina-form');
    if (nominaForm) {
        nominaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(nominaForm);
            fetch('/rrhh/api/nominas', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Nómina creada:', data);
                loadNominas();
                nominaForm.reset();
            })
            .catch(error => console.error('Error creando nómina:', error));
        });
    }
}

function initializeEvaluacionForm() {
    const evaluacionForm = document.getElementById('evaluacion-form');
    if (evaluacionForm) {
        evaluacionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(evaluacionForm);
            fetch('/rrhh/api/evaluaciones', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Evaluación creada:', data);
                loadEvaluaciones();
                evaluacionForm.reset();
            })
            .catch(error => console.error('Error creando evaluación:', error));
        });
    }
}

// Funciones específicas para el módulo de Compras
function initializeComprasModule() {
    const comprasContainer = document.getElementById('compras-container');
    if (comprasContainer) {
        loadSolicitudesCompra();
        loadOrdenesCompra();
        initializeSolicitudCompraForm();
        initializeOrdenCompraForm();
    }
}

function loadSolicitudesCompra() {
    fetch('/compras/api/solicitudes')
        .then(response => response.json())
        .then(solicitudes => {
            const solicitudesList = document.getElementById('solicitudes-list');
            if (solicitudesList) {
                solicitudesList.innerHTML = solicitudes.map(solicitud => 
                    `<li>${solicitud.numero} - ${solicitud.descripcion} - ${solicitud.estado}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading solicitudes de compra:', error));
}

function loadOrdenesCompra() {
    fetch('/compras/api/ordenes')
        .then(response => response.json())
        .then(ordenes => {
            const ordenesList = document.getElementById('ordenes-list');
            if (ordenesList) {
                ordenesList.innerHTML = ordenes.map(orden => 
                    `<li>${orden.numero} - ${orden.proveedor} - $${orden.total}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading órdenes de compra:', error));
}

function initializeSolicitudCompraForm() {
    const solicitudForm = document.getElementById('solicitud-compra-form');
    if (solicitudForm) {
        solicitudForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(solicitudForm);
            fetch('/compras/api/solicitudes', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Solicitud de compra creada:', data);
                loadSolicitudesCompra();
                solicitudForm.reset();
            })
            .catch(error => console.error('Error creando solicitud de compra:', error));
        });
    }
}

function initializeOrdenCompraForm() {
    const ordenForm = document.getElementById('orden-compra-form');
    if (ordenForm) {
        ordenForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(ordenForm);
            fetch('/compras/api/ordenes', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Orden de compra creada:', data);
                loadOrdenesCompra();
                ordenForm.reset();
            })
            .catch(error => console.error('Error creando orden de compra:', error));
        });
    }
}

// Funciones específicas para el módulo de Activos Fijos
// Funciones específicas para el módulo de Activos Fijos
function initializeActivosFijosModule() {
    const activosFijosContainer = document.getElementById('activos-fijos-container');
    if (activosFijosContainer) {
        loadActivosFijos();
        loadDepreciaciones();
        loadRetiros();
        loadRevalorizaciones();
        loadTiposActivoFijo();
        initializeActivoFijoForm();
        initializeDepreciacionForm();
        initializeRetiroForm();
        initializeRevalorizacionForm();
    }
}

function loadActivosFijos() {
    fetch('/activos_fijos/api/activos')
        .then(response => response.json())
        .then(activos => {
            const activosList = document.getElementById('activos-list');
            if (activosList) {
                activosList.innerHTML = activos.map(activo => 
                    `<li>${activo.nombre} - Valor: $${activo.valor} - Fecha adquisición: ${activo.fecha_adquisicion}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading activos fijos:', error));
}

function loadDepreciaciones() {
    fetch('/activos_fijos/api/depreciaciones')
        .then(response => response.json())
        .then(depreciaciones => {
            const depreciacionesList = document.getElementById('depreciaciones-list');
            if (depreciacionesList) {
                depreciacionesList.innerHTML = depreciaciones.map(depreciacion => 
                    `<li>Activo: ${depreciacion.activo} - Monto: $${depreciacion.monto} - Fecha: ${depreciacion.fecha}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading depreciaciones:', error));
}

function loadRetiros() {
    fetch('/activos_fijos/api/retiros')
        .then(response => response.json())
        .then(retiros => {
            const retirosList = document.getElementById('retiros-list');
            if (retirosList) {
                retirosList.innerHTML = retiros.map(retiro => 
                    `<li>Activo: ${retiro.activo} - Fecha: ${retiro.fecha} - Motivo: ${retiro.motivo}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading retiros:', error));
}

function loadRevalorizaciones() {
    fetch('/activos_fijos/api/revalorizaciones')
        .then(response => response.json())
        .then(revalorizaciones => {
            const revalorizacionesList = document.getElementById('revalorizaciones-list');
            if (revalorizacionesList) {
                revalorizacionesList.innerHTML = revalorizaciones.map(revalorizacion => 
                    `<li>Activo: ${revalorizacion.activo} - Nuevo valor: $${revalorizacion.nuevo_valor} - Fecha: ${revalorizacion.fecha}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading revalorizaciones:', error));
}

function loadTiposActivoFijo() {
    fetch('/activos_fijos/api/tipos')
        .then(response => response.json())
        .then(tipos => {
            const tiposList = document.getElementById('tipos-activo-fijo-list');
            if (tiposList) {
                tiposList.innerHTML = tipos.map(tipo => 
                    `<li>${tipo.nombre} - Vida útil: ${tipo.vida_util} años</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading tipos de activo fijo:', error));
}

function initializeActivoFijoForm() {
    const activoFijoForm = document.getElementById('activo-fijo-form');
    if (activoFijoForm) {
        activoFijoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(activoFijoForm);
            fetch('/activos_fijos/api/activos', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Activo fijo creado:', data);
                loadActivosFijos();
                activoFijoForm.reset();
            })
            .catch(error => console.error('Error creando activo fijo:', error));
        });
    }
}

function initializeDepreciacionForm() {
    const depreciacionForm = document.getElementById('depreciacion-form');
    if (depreciacionForm) {
        depreciacionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(depreciacionForm);
            fetch('/activos_fijos/api/depreciaciones', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Depreciación registrada:', data);
                loadDepreciaciones();
                depreciacionForm.reset();
            })
            .catch(error => console.error('Error registrando depreciación:', error));
        });
    }
}

function initializeRetiroForm() {
    const retiroForm = document.getElementById('retiro-form');
    if (retiroForm) {
        retiroForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(retiroForm);
            fetch('/activos_fijos/api/retiros', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Retiro registrado:', data);
                loadRetiros();
                retiroForm.reset();
            })
            .catch(error => console.error('Error registrando retiro:', error));
        });
    }
}

function initializeRevalorizacionForm() {
    const revalorizacionForm = document.getElementById('revalorizacion-form');
    if (revalorizacionForm) {
        revalorizacionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(revalorizacionForm);
            fetch('/activos_fijos/api/revalorizaciones', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Revalorización registrada:', data);
                loadRevalorizaciones();
                revalorizacionForm.reset();
            })
            .catch(error => console.error('Error registrando revalorización:', error));
        });
    }
}

// Funciones específicas para el módulo de Cuentas Por Pagar
function initializeCuentasPorPagarModule() {
    const cuentasPorPagarContainer = document.getElementById('cuentas-por-pagar-container');
    if (cuentasPorPagarContainer) {
        loadFacturasSuplidores();
        loadNotasCredito();
        loadNotasDebito();
        loadOrdenesCompra();
        loadSuplidores();
        loadAnticiposCxP();
        loadPagosContado();
        loadReportesCxP();
        loadRequisicionesCotizacion();
        loadSolicitudesCompra();
        loadTiposSuplidores();
    }
}

function loadFacturasSuplidores() {
    fetch('/cxp/api/facturas-suplidores')
        .then(response => response.json())
        .then(facturas => {
            const facturasList = document.getElementById('facturas-suplidores-list');
            if (facturasList) {
                facturasList.innerHTML = facturas.map(factura => 
                    `<li>Factura: ${factura.numero} - Suplidor: ${factura.suplidor} - Monto: $${factura.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading facturas de suplidores:', error));
}

function loadNotasCredito() {
    fetch('/cxp/api/notas-credito')
        .then(response => response.json())
        .then(notas => {
            const notasList = document.getElementById('notas-credito-list');
            if (notasList) {
                notasList.innerHTML = notas.map(nota => 
                    `<li>Nota de Crédito: ${nota.numero} - Suplidor: ${nota.suplidor} - Monto: $${nota.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading notas de crédito:', error));
}

function loadNotasDebito() {
    fetch('/cxp/api/notas-debito')
        .then(response => response.json())
        .then(notas => {
            const notasList = document.getElementById('notas-debito-list');
            if (notasList) {
                notasList.innerHTML = notas.map(nota => 
                    `<li>Nota de Débito: ${nota.numero} - Suplidor: ${nota.suplidor} - Monto: $${nota.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading notas de débito:', error));
}

function loadSuplidores() {
    fetch('/cxp/api/suplidores')
        .then(response => response.json())
        .then(suplidores => {
            const suplidoresList = document.getElementById('suplidores-list');
            if (suplidoresList) {
                suplidoresList.innerHTML = suplidores.map(suplidor => 
                    `<li>${suplidor.nombre} - RNC: ${suplidor.rnc} - Teléfono: ${suplidor.telefono}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading suplidores:', error));
}

function loadAnticiposCxP() {
    fetch('/cxp/api/anticipos')
        .then(response => response.json())
        .then(anticipos => {
            const anticiposList = document.getElementById('anticipos-cxp-list');
            if (anticiposList) {
                anticiposList.innerHTML = anticipos.map(anticipo => 
                    `<li>Anticipo: ${anticipo.numero} - Suplidor: ${anticipo.suplidor} - Monto: $${anticipo.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading anticipos CxP:', error));
}

function loadPagosContado() {
    fetch('/cxp/api/pagos-contado')
        .then(response => response.json())
        .then(pagos => {
            const pagosList = document.getElementById('pagos-contado-list');
            if (pagosList) {
                pagosList.innerHTML = pagos.map(pago => 
                    `<li>Pago: ${pago.numero} - Suplidor: ${pago.suplidor} - Monto: $${pago.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading pagos de contado:', error));
}

function loadReportesCxP() {
    fetch('/cxp/api/reportes')
        .then(response => response.json())
        .then(reportes => {
            const reportesList = document.getElementById('reportes-cxp-list');
            if (reportesList) {
                reportesList.innerHTML = reportes.map(reporte => 
                    `<li>Reporte: ${reporte.nombre} - Fecha: ${reporte.fecha}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading reportes CxP:', error));
}

function loadRequisicionesCotizacion() {
    fetch('/cxp/api/requisiciones-cotizacion')
        .then(response => response.json())
        .then(requisiciones => {
            const requisicionesList = document.getElementById('requisiciones-cotizacion-list');
            if (requisicionesList) {
                requisicionesList.innerHTML = requisiciones.map(requisicion => 
                    `<li>Requisición: ${requisicion.numero} - Descripción: ${requisicion.descripcion}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading requisiciones de cotización:', error));
}

function loadTiposSuplidores() {
    fetch('/cxp/api/tipos-suplidores')
        .then(response => response.json())
        .then(tipos => {
            const tiposList = document.getElementById('tipos-suplidores-list');
            if (tiposList) {
                tiposList.innerHTML = tipos.map(tipo => 
                    `<li>${tipo.nombre}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading tipos de suplidores:', error));
}

// Funciones específicas para el módulo de Importación
function initializeImportacionModule() {
    const importacionContainer = document.getElementById('importacion-container');
    if (importacionContainer) {
        loadExpedientes();
        loadImportadores();
        loadReportesImportacion();
        initializeExpedienteForm();
        initializeImportadorForm();
    }
}

function loadExpedientes() {
    fetch('/importacion/api/expedientes')
        .then(response => response.json())
        .then(expedientes => {
            const expedientesList = document.getElementById('expedientes-list');
            if (expedientesList) {
                expedientesList.innerHTML = expedientes.map(expediente => 
                    `<li>Expediente: ${expediente.numero} - Estado: ${expediente.estado}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading expedientes:', error));
}

function loadImportadores() {
    fetch('/importacion/api/importadores')
        .then(response => response.json())
        .then(importadores => {
            const importadoresList = document.getElementById('importadores-list');
            if (importadoresList) {
                importadoresList.innerHTML = importadores.map(importador => 
                    `<li>${importador.nombre} - RNC: ${importador.rnc}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading importadores:', error));
}

function loadReportesImportacion() {
    fetch('/importacion/api/reportes')
        .then(response => response.json())
        .then(reportes => {
            const reportesList = document.getElementById('reportes-importacion-list');
            if (reportesList) {
                reportesList.innerHTML = reportes.map(reporte => 
                    `<li>Reporte: ${reporte.nombre} - Fecha: ${reporte.fecha}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading reportes de importación:', error));
}

function initializeExpedienteForm() {
    const expedienteForm = document.getElementById('expediente-form');
    if (expedienteForm) {
        expedienteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(expedienteForm);
            fetch('/importacion/api/expedientes', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Expediente creado:', data);
                loadExpedientes();
                expedienteForm.reset();
            })
            .catch(error => console.error('Error creando expediente:', error));
        });
    }
}

function initializeImportadorForm() {
    const importadorForm = document.getElementById('importador-form');
    if (importadorForm) {
        importadorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(importadorForm);
            fetch('/importacion/api/importadores', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Importador creado:', data);
                loadImportadores();
                importadorForm.reset();
            })
            .catch(error => console.error('Error creando importador:', error));
        });
    }
}

// Funciones específicas para el módulo de Proyectos
function initializeProyectosModule() {
    const proyectosContainer = document.getElementById('proyectos-container');
    if (proyectosContainer) {
        loadProyectos();
        loadPresupuestos();
        loadFacturacion();
        initializeProyectoForm();
        initializePresupuestoForm();
    }
}

function loadProyectos() {
    fetch('/proyectos/api/proyectos')
        .then(response => response.json())
        .then(proyectos => {
            const proyectosList = document.getElementById('proyectos-list');
            if (proyectosList) {
                proyectosList.innerHTML = proyectos.map(proyecto => 
                    `<li>${proyecto.nombre} - Estado: ${proyecto.estado}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading proyectos:', error));
}

function loadPresupuestos() {
    fetch('/proyectos/api/presupuestos')
        .then(response => response.json())
        .then(presupuestos => {
            const presupuestosList = document.getElementById('presupuestos-list');
            if (presupuestosList) {
                presupuestosList.innerHTML = presupuestos.map(presupuesto => 
                    `<li>Proyecto: ${presupuesto.proyecto_nombre} - Monto: ${presupuesto.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading presupuestos:', error));
}

function loadFacturacion() {
    fetch('/proyectos/api/facturacion')
        .then(response => response.json())
        .then(facturas => {
            const facturasList = document.getElementById('facturas-list');
            if (facturasList) {
                facturasList.innerHTML = facturas.map(factura => 
                    `<li>Factura: ${factura.numero_factura} - Monto: ${factura.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading facturación:', error));
}

function initializeProyectoForm() {
    const proyectoForm = document.getElementById('proyecto-form');
    if (proyectoForm) {
        proyectoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(proyectoForm);
            fetch('/proyectos/api/proyectos', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Proyecto creado:', data);
                loadProyectos();
                proyectoForm.reset();
            })
            .catch(error => console.error('Error creando proyecto:', error));
        });
    }
}

function initializePresupuestoForm() {
    const presupuestoForm = document.getElementById('presupuesto-form');
    if (presupuestoForm) {
        presupuestoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(presupuestoForm);
            fetch('/proyectos/api/presupuestos', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Presupuesto creado:', data);
                loadPresupuestos();
                presupuestoForm.reset();
            })
            .catch(error => console.error('Error creando presupuesto:', error));
        });
    }
}

// Funciones específicas para el módulo de Cuentas Por Cobrar
function initializeCuentasPorCobrarModule() {
    const cxcContainer = document.getElementById('cxc-container');
    if (cxcContainer) {
        loadClientes();
        loadDescuentosDevoluciones();
        loadNotasCredito();
        loadNotasDebito();
        loadRecibos();
        loadAnticipos();
        loadCondicionesPago();
        loadReporteCxC();
        loadTiposCliente();
        initializeClienteForm();
        initializeNotaCreditoForm();
        initializeNotaDebitoForm();
        initializeReciboForm();
    }
}

function loadClientes() {
    fetch('/cxc/api/clientes')
        .then(response => response.json())
        .then(clientes => {
            const clientesList = document.getElementById('clientes-list');
            if (clientesList) {
                clientesList.innerHTML = clientes.map(cliente => 
                    `<li>${cliente.nombre} - ${cliente.email}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading clientes:', error));
}

function loadDescuentosDevoluciones() {
    fetch('/cxc/api/descuentos-devoluciones')
        .then(response => response.json())
        .then(descuentosDevoluciones => {
            const descuentosDevolucionesList = document.getElementById('descuentos-devoluciones-list');
            if (descuentosDevolucionesList) {
                descuentosDevolucionesList.innerHTML = descuentosDevoluciones.map(dd => 
                    `<li>${dd.tipo} - $${dd.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading descuentos y devoluciones:', error));
}

function loadNotasCredito() {
    fetch('/cxc/api/notas-credito')
        .then(response => response.json())
        .then(notasCredito => {
            const notasCreditoList = document.getElementById('notas-credito-list');
            if (notasCreditoList) {
                notasCreditoList.innerHTML = notasCredito.map(nota => 
                    `<li>Nota de Crédito #${nota.id} - $${nota.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading notas de crédito:', error));
}

function loadNotasDebito() {
    fetch('/cxc/api/notas-debito')
        .then(response => response.json())
        .then(notasDebito => {
            const notasDebitoList = document.getElementById('notas-debito-list');
            if (notasDebitoList) {
                notasDebitoList.innerHTML = notasDebito.map(nota => 
                    `<li>Nota de Débito #${nota.id} - $${nota.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading notas de débito:', error));
}

function loadRecibos() {
    fetch('/cxc/api/recibos')
        .then(response => response.json())
        .then(recibos => {
            const recibosList = document.getElementById('recibos-list');
            if (recibosList) {
                recibosList.innerHTML = recibos.map(recibo => 
                    `<li>Recibo #${recibo.id} - $${recibo.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading recibos:', error));
}

function loadAnticipos() {
    fetch('/cxc/api/anticipos')
        .then(response => response.json())
        .then(anticipos => {
            const anticiposList = document.getElementById('anticipos-list');
            if (anticiposList) {
                anticiposList.innerHTML = anticipos.map(anticipo => 
                    `<li>Anticipo para ${anticipo.cliente} - $${anticipo.monto}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading anticipos:', error));
}

function loadCondicionesPago() {
    fetch('/cxc/api/condiciones-pago')
        .then(response => response.json())
        .then(condiciones => {
            const condicionesList = document.getElementById('condiciones-pago-list');
            if (condicionesList) {
                condicionesList.innerHTML = condiciones.map(condicion => 
                    `<li>${condicion.nombre} - ${condicion.dias} días</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading condiciones de pago:', error));
}

function loadReporteCxC() {
    fetch('/cxc/api/reporte')
        .then(response => response.json())
        .then(reporte => {
            const reporteContainer = document.getElementById('reporte-cxc-container');
            if (reporteContainer) {
                reporteContainer.innerHTML = `
                    <h2>Resumen de Cuentas por Cobrar</h2>
                    <p>Total por cobrar: $${reporte.total_por_cobrar}</p>
                    <p>Cuentas vencidas: $${reporte.cuentas_vencidas}</p>
                    <p>Cuentas por vencer: $${reporte.cuentas_por_vencer}</p>
                `;
            }
        })
        .catch(error => console.error('Error loading reporte CxC:', error));
}

function loadTiposCliente() {
    fetch('/cxc/api/tipos-cliente')
        .then(response => response.json())
        .then(tipos => {
            const tiposClienteList = document.getElementById('tipos-cliente-list');
            if (tiposClienteList) {
                tiposClienteList.innerHTML = tipos.map(tipo => 
                    `<li>${tipo.nombre}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading tipos de cliente:', error));
}

function initializeClienteForm() {
    const clienteForm = document.getElementById('cliente-form');
    if (clienteForm) {
        clienteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(clienteForm);
            fetch('/cxc/api/clientes', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Cliente creado:', data);
                loadClientes();
                clienteForm.reset();
            })
            .catch(error => console.error('Error creando cliente:', error));
        });
    }
}

function initializeNotaCreditoForm() {
    const notaCreditoForm = document.getElementById('nota-credito-form');
    if (notaCreditoForm) {
        notaCreditoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(notaCreditoForm);
            fetch('/cxc/api/notas-credito', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Nota de crédito creada:', data);
                loadNotasCredito();
                notaCreditoForm.reset();
            })
            .catch(error => console.error('Error creando nota de crédito:', error));
        });
    }
}

function initializeNotaDebitoForm() {
    const notaDebitoForm = document.getElementById('nota-debito-form');
    if (notaDebitoForm) {
        notaDebitoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(notaDebitoForm);
            fetch('/cxc/api/notas-debito', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Nota de débito creada:', data);
                loadNotasDebito();
                notaDebitoForm.reset();
            })
            .catch(error => console.error('Error creando nota de débito:', error));
        });
    }
}

function initializeReciboForm() {
    const reciboForm = document.getElementById('recibo-form');
    if (reciboForm) {
        reciboForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(reciboForm);
            fetch('/cxc/api/recibos', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Recibo creado:', data);
                loadRecibos();
                reciboForm.reset();
            })
            .catch(error => console.error('Error creando recibo:', error));
        });
    }
}

// Funciones específicas para el módulo de Inventario
function initializeInventarioModule() {
    const inventarioContainer = document.getElementById('inventario-container');
    if (inventarioContainer) {
        loadItems();
        loadEntradasAlmacen();
        loadSalidasAlmacen();
        loadInventario();
        loadReporteInventario();
        initializeItemForm();
        initializeEntradaAlmacenForm();
        initializeSalidaAlmacenForm();
    }
}

function loadItems() {
    fetch('/inventario/api/items')
        .then(response => response.json())
        .then(items => {
            const itemsList = document.getElementById('items-list');
            if (itemsList) {
                itemsList.innerHTML = items.map(item => 
                    `<li>${item.nombre} - Código: ${item.codigo} - Stock: ${item.stock}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading items:', error));
}

function loadEntradasAlmacen() {
    fetch('/inventario/api/entradas-almacen')
        .then(response => response.json())
        .then(entradas => {
            const entradasList = document.getElementById('entradas-almacen-list');
            if (entradasList) {
                entradasList.innerHTML = entradas.map(entrada => 
                    `<li>Entrada #${entrada.id} - Item: ${entrada.item_nombre} - Cantidad: ${entrada.cantidad}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading entradas de almacén:', error));
}

function loadSalidasAlmacen() {
    fetch('/inventario/api/salidas-almacen')
        .then(response => response.json())
        .then(salidas => {
            const salidasList = document.getElementById('salidas-almacen-list');
            if (salidasList) {
                salidasList.innerHTML = salidas.map(salida => 
                    `<li>Salida #${salida.id} - Item: ${salida.item_nombre} - Cantidad: ${salida.cantidad}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading salidas de almacén:', error));
}

function loadInventario() {
    fetch('/inventario/api/inventario')
        .then(response => response.json())
        .then(inventario => {
            const inventarioList = document.getElementById('inventario-list');
            if (inventarioList) {
                inventarioList.innerHTML = inventario.map(item => 
                    `<li>${item.nombre} - Stock: ${item.stock} - Valor: $${item.valor_total}</li>`
                ).join('');
            }
        })
        .catch(error => console.error('Error loading inventario:', error));
}

function loadReporteInventario() {
    fetch('/inventario/api/reporte')
        .then(response => response.json())
        .then(reporte => {
            const reporteContainer = document.getElementById('reporte-inventario-container');
            if (reporteContainer) {
                reporteContainer.innerHTML = `
                    <h2>Resumen de Inventario</h2>
                    <p>Total de items: ${reporte.total_items}</p>
                    <p>Valor total del inventario: $${reporte.valor_total}</p>
                    <p>Items con bajo stock: ${reporte.items_bajo_stock}</p>
                `;
            }
        })
        .catch(error => console.error('Error loading reporte de inventario:', error));
}

function initializeItemForm() {
    const itemForm = document.getElementById('item-form');
    if (itemForm) {
        itemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(itemForm);
            fetch('/inventario/api/items', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Item creado:', data);
                loadItems();
                itemForm.reset();
            })
            .catch(error => console.error('Error creando item:', error));
        });
    }
}

function initializeEntradaAlmacenForm() {
    const entradaForm = document.getElementById('entrada-almacen-form');
    if (entradaForm) {
        entradaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(entradaForm);
            fetch('/inventario/api/entradas-almacen', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Entrada de almacén registrada:', data);
                loadEntradasAlmacen();
                loadInventario();
                entradaForm.reset();
            })
            .catch(error => console.error('Error registrando entrada de almacén:', error));
        });
    }
}

function initializeSalidaAlmacenForm() {
    const salidaForm = document.getElementById('salida-almacen-form');
    if (salidaForm) {
        salidaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(salidaForm);
            fetch('/inventario/api/salidas-almacen', {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Salida de almacén registrada:', data);
                loadSalidasAlmacen();
                loadInventario();
                salidaForm.reset();
            })
            .catch(error => console.error('Error registrando salida de almacén:', error));
        });
    }
}

// Inicialización del sistema
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
    loadModules();
    loadTasks();
    loadNotifications();
    initializeCharts();
    initializeCalendar();
    initializeAsistente();
    initializeSubmoduleHandlers();
    initializeAuthForms();
    initializeMarketingModule();
    initializeRRHHModule();
    initializeComprasModule();
    initializeActivosFijosModule();
    initializeCuentasPorPagarModule();
    initializeImportacionModule();
    initializeProyectosModule();
    initializeCuentasPorCobrarModule();
    initializeInventarioModule();
    window.addEventListener('resize', resizeCharts);

    ['line', 'bar', 'pie'].forEach(type => {
        const toggleButton = document.getElementById(`toggle-${type}-chart`);
        if (toggleButton) {
            toggleButton.addEventListener('click', () => toggleChartVisibility(`${type}-chart`));
        }
    });

    console.log('Sistema inicializado correctamente');
});

// Función para manejar errores globales
window.onerror = function(message, source, lineno, colno, error) {
    console.error('Error global capturado:', message, 'en', source, 'línea:', lineno);
    // Aquí podrías implementar un sistema de logging de errores o notificaciones al usuario
};

// Exportar funciones que puedan ser necesarias en otros scripts
window.CalculAI = {
    loadUserInfo,
    loadModules,
    initializeAsistente,
    handleLogout,
    // ... otras funciones que necesites exponer
};