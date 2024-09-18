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
}

// Maneja el clic en submódulos
function handleSubmoduleClick(moduleName, submoduleName) {
    console.log(`Clicked on ${submoduleName} of ${moduleName}`);
    if (moduleName === 'Banco' && submoduleName === 'Bancos') {
        window.location.href = '/Bancos';
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
            const colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#FFC0CB", "#98D8C8", "#F06292", "#AED581", "#FFD54F", "#800000", "#4DB6AC", "#075e56"];
            modulos.forEach((modulo, index) => {
                const moduleDiv = createModuleElement(modulo, colors[index % colors.length]);
                moduleContainer.appendChild(moduleDiv);
            });
        })
        .catch(error => console.error('Error loading modules:', error));
}

// Crea un elemento HTML para un módulo
function createModuleElement(modulo, color) {
    const moduleDiv = document.createElement('div');
    moduleDiv.className = 'module-wrapper';
    
    const button = createButton(modulo, 'rectangular-button', color);
    button.onclick = () => toggleSubmodules(modulo, moduleDiv);
    
    const submoduleContainer = document.createElement('div');
    submoduleContainer.className = 'submodule-container';
    
    moduleDiv.appendChild(button);
    moduleDiv.appendChild(submoduleContainer);
    return moduleDiv;
}

// Crea un botón genérico
function createButton(text, className, color) {
    const button = document.createElement('button');
    button.textContent = text;
    button.className = className;
    if (color) button.style.backgroundColor = color;
    if (className === 'submodule-button') {
        button.style.width = 'auto';
    }
    return button;
}

// Alterna la visibilidad de los submódulos
function toggleSubmodules(moduleName, moduleDiv) {
    const submoduleContainer = moduleDiv.querySelector('.submodule-container');
    const moduleButton = moduleDiv.querySelector('.rectangular-button');
    const isOpen = submoduleContainer.style.display === 'block';

    document.querySelectorAll('.submodule-container').forEach(container => {
        if (container !== submoduleContainer) {
            container.style.display = 'none';
        }
    });
    document.querySelectorAll('.rectangular-button').forEach(btn => {
        if (btn !== moduleButton) {
            btn.classList.remove('active');
        }
    });

    if (!isOpen) {
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
                    const button = createButton(submodulo, 'submodule-button');
                    button.onclick = (event) => {
                        event.preventDefault();
                        handleSubmoduleClick(moduleName, submodulo);
                    };
                    submoduleContainer.appendChild(button);
                });
            })
            .catch(error => console.error('Error loading submodules:', error));
    }
}

// Carga el contenido de un submódulo específico
function loadSubmoduleContent(moduleName, submoduleName) {
    console.log(`Loading content for ${moduleName} - ${submoduleName}`);
    // Implementar lógica para cargar contenido del submódulo
    // Por ejemplo:
    fetch(`/api/submodule-content/${moduleName}/${submoduleName}`)
        .then(response => response.json())
        .then(data => {
            // Actualizar el contenido en la interfaz de usuario
            const contentContainer = document.getElementById('submodule-content');
            if (contentContainer) {
                contentContainer.innerHTML = data.content;
            }
        })
        .catch(error => console.error('Error loading submodule content:', error));
}

// Carga las tareas pendientes desde la API
function loadTasks() {
    fetch('/api/tareas')
        .then(response => response.json())
        .then(tareas => {
            const taskList = document.getElementById('task-list');
            taskList.innerHTML = tareas.map(tarea => 
                `<li>${tarea.descripcion} - Vence: ${new Date(tarea.vence).toLocaleDateString()}</li>`
            ).join('');
        })
        .catch(error => console.error('Error loading tasks:', error));
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

    // Comprobar si el asistente está activo (esto dependerá de cómo manejes el estado del asistente)
    fetch('/api/asistente-status')
        .then(response => response.json())
        .then(data => {
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