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
        if (data.respuesta) {
            mostrarMensajeAsistente(data.respuesta);
        }
    })
    .catch(error => console.error('Error:', error));
}

// Función para mostrar mensajes del asistente
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
    } else {
        console.log('Mensaje del asistente:', mensaje);
    }
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

    }else if (moduleName === 'Cuentas Por Pagar') {
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
    }else if (moduleName === 'Activos Fijos') {
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
            
    
            
        
    }else if (moduleName === 'Importacion') {
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
    
    }else if (moduleName === 'Cuentas Por Cobrar') {
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
        
    }else if (moduleName === 'Impuestos') {
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

    }else if (moduleName === 'Recursos Humanos') {
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
        
    }else if (moduleName === 'Proyectos') {
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
          
    }else if (moduleName === 'Cuentas Por Cobrar') {
        switch (submoduleName) {
            case 'Cliente':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Cliente');
                break;
            case 'Descuento y devoluciones':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Descuento y devoluciones');
                break;
            case 'Nota de credito':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Nota de credito');
                break;
            case 'Nota de debito':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Nota de debito');
                break;
            case 'Recibo':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Recibo');
                break;
            case 'Anticipo CxC':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Anticipo CxC');
                break;
            case 'Condicion de pago':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Condicion de pago');
                break;
            case 'Reporte CxC':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Reporte CxC');
                break;
            case 'Tipo de cliente':
                loadSubmoduleContent('Cuentas Por Cobrar', 'Tipo de cliente');
                break;
            default:
                console.log('Submódulo de Cuentas Por Cobrar no reconocido');
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
        // Manejar otros submódulos aquí
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
    
    let url;
    if (moduleName === 'Facturacion') {
        switch (submoduleName) {
            case 'Facturas':
                url = '/facturacion/facturas';
                break;
            case 'Pre-facturas':
                url = '/facturacion/pre-facturas';
                break;
            case 'Notas de Crédito/Débito':
                url = '/facturacion/notas-de-credito-debito';
                break;
            case 'Reporte de Ventas':
                url = '/facturacion/reporte-de-ventas';
                break;
            case 'Gestión de Clientes':
                url = '/facturacion/gestion-de-clientes';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }

    }else if (moduleName === 'Cuentas Por Pagar') {
        switch (submoduleName) {
            case 'Factura Suplidor':
                url = '/cxp/factura-suplidor';
                break;
            case 'Nota de Crédito':
                url = '/cxp/nota-credito';
                break;
            case 'Nota de Débito':
                url = '/cxp/nota-debito';
                break;
            case 'Orden de Compras':
                url = '/cxp/orden-compras';
                break;
            case 'Suplidor':
                url = '/cxp/suplidor';
                break;
            case 'Anticipo CxP':
                url = '/cxp/anticipo-cxp';
                break;
            case 'Pago de Contado':
                url = '/cxp/pago-contado';
                break;
            case 'Reporte CxP':
                url = '/cxp/reporte-cxp';
                break;
            case 'Requisición Cotización':
                url = '/cxp/requisicion-cotizacion';
                break;
            case 'Solicitud Compras':
                url = '/cxp/solicitud-compras';
                break;
            case 'Tipo de Suplidor':
                url = '/cxp/tipo-suplidor';
                break;
            default:
        }     url = `/api/submodule-content/${moduleName}/${submoduleName}`;
                
    }else if (moduleName === 'Activos Fijos') {
        switch (submoduleName) {
            case 'Activo Fijo':
                url = '/activos_fijos/activo_fijo';
                break;
            case 'Depreciación':
                url = '/activos_fijos/depreciacion';
                break;
            case 'Retiro':
                url = '/activos_fijos/retiro';
                break;
            case 'Revalorización':
                url = '/activos_fijos/revalorizacion';
                break;
            case 'Tipo de Activo Fijo':
                url = '/activos_fijos/tipo_activo_fijo';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
            
    }else if (moduleName === 'Cuentas Por Cobrar') {
        switch (submoduleName) {
            case 'Cliente':
                url = '/cxc/clientes';
                break;
            case 'Descuento y devoluciones':
                url = '/cxc/descuentos-devoluciones';
                break;
            case 'Nota de credito':
                url = '/cxc/notas-credito';
                break;
            case 'Nota de debito':
                url = '/cxc/notas-debito';
                break;
            case 'Recibo':
                url = '/cxc/recibos';
                break;
            case 'Anticipo CxC':
                url = '/cxc/anticipos';
                break;
            case 'Condicion de pago':
                url = '/cxc/condiciones-pago';
                break;
            case 'Reporte CxC':
                url = '/cxc/reporte';
                break;
            case 'Tipo de cliente':
                url = '/cxc/tipos-cliente';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
            
       
    }else if (moduleName === 'Impuestos') {
        switch (submoduleName) {
            case 'Formulario 606':
                url = '/impuestos/formulario606';
                break;
            case 'Formulario 607':
                url = '/impuestos/formulario607';
                break;
            case 'Reporte IT1':
                url = '/impuestos/reporte-it1';
                break;
            case 'Impuesto sobre la Renta (IR17)':
                url = '/impuestos/ir17';
                break;
            case 'Serie Fiscal':
                url = '/impuestos/serie-fiscal';
                break;
            case 'Configuraciones':
                url = '/impuestos/configuraciones';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
       
        
    }else if (moduleName === 'Proyectos') {
        switch (submoduleName) {
            case 'Gestión de Proyectos':
                url = '/proyectos/gestion';
                break;
            case 'Presupuestos':
                url = '/proyectos/presupuestos';
                break;
            case 'Facturación por Proyecto':
                url = '/proyectos/facturacion';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
    }else if (moduleName === 'Importacion') {
        switch (submoduleName) {
            case 'Expediente de Importacion':
                url = '/importacion/expediente';
                break;
            case 'Importador':
                url = '/importacion/importador';
                break;
            case 'Reportes Importacion':
                url = '/importacion/reportes';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
        
    } else if (moduleName === 'Inventario') {
        switch (submoduleName) {
            case 'Items':
                url = '/inventario/items';
                break;
            case 'Entrada de Almacén':
                url = '/inventario/entrada-almacen';
                break;
            case 'Salida de Almacén':
                url = '/inventario/salida-almacen';
                break;
            case 'Inventario':
                url = '/inventario/inventario';
                break;
            case 'Reporte de Inventario':
                url = '/inventario/reporte';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
    } else if (moduleName === 'Marketing') {
        switch (submoduleName) {
            case 'Gestión de Contactos':
                url = '/marketing/contacts';
                break;
            case 'Campañas de Email':
                url = '/marketing/campaigns';
                break;
            case 'Plantillas de Email':
                url = '/marketing/templates';
                break;
            case 'Reportes de Campañas':
                url = '/marketing/reports';
                break;
            case 'Segmentación de Contactos':
                url = '/marketing/segmentation';
                break;
            case 'Automatizaciones':
                url = '/marketing/automations';
                break;
            case 'Integración de Redes Sociales':
                url = '/marketing/social-media';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }

    } else if (moduleName === 'Compras') {
        switch (submoduleName) {
            case 'Solicitudes de Compra':
                url = '/compras/solicitudes';
                break;
            case 'Órdenes de Compra':
                url = '/compras/ordenes';
                break;
            case 'Recepción de Materiales':
                url = '/compras/recepcion';
                break;
            case 'Gastos':
                url = '/compras/gastos';
                break;
            case 'Reporte de Compras/Gastos':
                url = '/compras/reporte';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
  
    }else if (moduleName === 'Recursos Humanos') {
        switch (submoduleName) {
            case 'Gestión de Empleados':
                url = '/rrhh/empleados';
                break;
            case 'Nómina':
                url = '/rrhh/nomina';
                break;
            case 'Evaluación de Desempeño':
                url = '/rrhh/evaluacion';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
    } else if (moduleName === 'Contabilidad') {
        switch (submoduleName) {
            case 'Cuentas':
                url = '/contabilidad/cuentas';
                break;
            case 'Diario':
                url = '/contabilidad/diario';
                break;
            case 'Mayor General':
                url = '/contabilidad/mayor_general';
                break;
            case 'Balanza de Comprobación':
                url = '/contabilidad/balanza_comprobacion';
                break;
            case 'Estado de Resultados':
                url = '/contabilidad/estado_resultados';
                break;
            case 'Balance General':
                url = '/contabilidad/balance_general';
                break;
            case 'Configuraciones':
                url = '/contabilidad/configuraciones';
                break;
            case 'Flujo de caja':
                url = '/contabilidad/flujo_caja';
                break;
            default:
                url = `/api/submodule-content/${moduleName}/${submoduleName}`;
        }
    } else {
        url = `/api/submodule-content/${moduleName}/${submoduleName}`;
    }
        
    
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
    const asistenteInput = document.getElementById('asistente-input');
    const asistenteEnviar = document.getElementById('asistente-enviar');

    // Comprobar si el asistente está activo
    fetch('/api/asistente_status')
        .then(response => response.json())
        .then(data => {
            console.log('Estado del asistente:', data);
            const asistenteActivo = data.activo;
            if (!asistenteActivo) {
                chatWindow.classList.add('asistente-inactivo');
                mostrarMensajeAsistente("El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.");
            }
        })
        .catch(error => {
            console.error('Error al verificar el estado del asistente:', error);
            chatWindow.classList.add('asistente-inactivo');
            mostrarMensajeAsistente("Error al verificar el estado del asistente. Por favor, intente más tarde.");
        });

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

// Funciones específicas para el módulo de Compras
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

function initializeActivosFijosModule() {
    const activosFijosContainer = document.getElementById('activos-fijos-container');
    if (activosFijosContainer) {
        loadActivosFijos();
        loadDepreciaciones();
        loadRetiros();
        loadRevalorizaciones();
        loadTiposActivoFijo();
    }
}

function loadActivosFijos() {
    // Lógica para cargar activos fijos
}

function loadDepreciaciones() {
    // Lógica para cargar depreciaciones
}

function loadRetiros() {
    // Lógica para cargar retiros
}

function loadRevalorizaciones() {
    // Lógica para cargar revalorizaciones
}

function loadTiposActivoFijo() {
    // Lógica para cargar tipos de activo fijo
}

// Asegúrate de llamar a esta función cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    // ... otras inicializaciones ...
    initializeActivosFijosModule();
});

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
    // Lógica para cargar facturas de suplidores
}

function loadNotasCredito() {
    // Lógica para cargar notas de crédito
}

function loadNotasDebito() {
    // Lógica para cargar notas de débito
}

function loadOrdenesCompra() {
    // Lógica para cargar órdenes de compra
}

function loadSuplidores() {
    // Lógica para cargar suplidores
}

function loadAnticiposCxP() {
    // Lógica para cargar anticipos CxP
}

function loadPagosContado() {
    // Lógica para cargar pagos de contado
}

function loadReportesCxP() {
    // Lógica para cargar reportes CxP
}

function loadRequisicionesCotizacion() {
    // Lógica para cargar requisiciones de cotización
}

function loadSolicitudesCompra() {
    // Lógica para cargar solicitudes de compra
}

function loadTiposSuplidores() {
    // Lógica para cargar tipos de suplidores
}

// Asegúrate de llamar a esta función cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    // ... otras inicializaciones ...
    initializeCuentasPorPagarModule();
});

function initializeImportacionModule() {
    const importacionContainer = document.getElementById('importacion-container');
    if (importacionContainer) {
        loadExpedientes();
        loadImportadores();
        loadReportesImportacion();
    }
}

function loadExpedientes() {
    // Lógica para cargar expedientes
}

function loadImportadores() {
    // Lógica para cargar importadores
}

function loadReportesImportacion() {
    // Lógica para cargar reportes de importación
}

// Asegúrate de llamar a esta función cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    // ... otras inicializaciones ...
    initializeImportacionModule();
});

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

function initializeProyectosModule() {
    const proyectosContainer = document.getElementById('proyectos-container');
    if (proyectosContainer) {
        loadProyectos();
        loadPresupuestos();
        loadFacturacion();
    }
}

function loadProyectos() {
    fetch('/proyectos/api/proyectos')
        .then(response => response.json())
        .then(proyectos => {
            const proyectosList = document.getElementById('proyectos-list');
            if (proyectosList) {
                proyectosList.innerHTML = proyectos.map(proyecto => 
                    `<li>${proyecto.nombre} - ${proyecto.estado}</li>`
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

// Asegúrate de llamar a esta función cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    // ... otras inicializaciones ...
    initializeProyectosModule();
});

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





// Asegúrate de llamar a initializeSubmoduleHandlers cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeSubmoduleHandlers();
    // Otras inicializaciones...
});
// Asegúrate de llamar a esta función cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    // ... otras inicializaciones ...
    initializeCuentasPorCobrarModule();
});
// Asegúrate de llamar a esta función cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    // ... otras inicializaciones ...
    initializeComprasModule();
});

// Asegúrate de llamar a estas nuevas funciones cuando sea necesario
document.addEventListener('DOMContentLoaded', function() {
    initializeMarketingModule();
    initializeEmailTemplateEditor();
    loadContactSegmentation();
    initializeMarketingAutomations();
    initializeSocialMediaIntegration();
});