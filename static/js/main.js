// Espera a que el DOM esté completamente cargado antes de ejecutar las funciones
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();       // Carga la información del usuario
    loadModules();        // Carga los módulos del sistema
    loadTasks();          // Carga las tareas pendientes
    loadNotifications();  // Carga las notificaciones
    initializeCharts();   // Inicializa los gráficos
    initializeCalendar(); // Inicializa el calendario
    initializeAsistente();// Inicializa el asistente virtual
    initializeSubmoduleHandlers(); // Inicializa los manejadores de submódulos
    window.addEventListener('resize', resizeCharts); // Ajusta los gráficos al redimensionar la ventana

    // Agrega event listeners para mostrar/ocultar gráficos
    ['line', 'bar', 'pie'].forEach(type => {
        const toggleButton = document.getElementById(`toggle-${type}-chart`);
        if (toggleButton) {
            toggleButton.addEventListener('click', () => toggleChartVisibility(`${type}-chart`));
        }
    });
});

// Función para notificar al asistente virtual
function notificarAsistente(mensaje) {
    fetch('/api/asistente', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pregunta: mensaje })
    })
    .then(response => response.json())
    .then(data => {
        if (data.respuesta) {
            if (data.respuesta === "El asistente virtual está desactivado en este momento.") {
                mostrarMensajeAsistente("El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.");
            } else {
                mostrarMensajeAsistente(data.respuesta);
            }
        }
    })
    .catch(error => console.error('Error al notificar al asistente:', error));
}

// Función para mostrar mensajes del asistente
function mostrarMensajeAsistente(mensaje) {
    const mensajesDiv = document.getElementById('asistente-mensajes');
    if (mensajesDiv) {
        const nuevoMensaje = document.createElement('div');
        if (mensaje === "El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.") {
            nuevoMensaje.innerHTML = `
                <p class="asistente-inactivo">
                    <span style="color: #ff0000; font-weight: bold;">El asistente no está activo.</span><br>
                    Por favor, contacte al <span style="color: #0000ff;">equipo de CalculAI</span> para su activación.
                </p>
            `;
        } else {
            nuevoMensaje.textContent = mensaje;
        }
        mensajesDiv.appendChild(nuevoMensaje);
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;  // Scroll al final del chat
    } else {
        console.log('Mensaje del asistente:', mensaje);
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
            title: { display: true, text: 'Ventas' }
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
            title: { display: true, text: 'Ingresos vs Gastos' }
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
            title: { display: true, text: 'Distribución' }
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
    const asistenteActivo = false; // Esto debería ser una variable o función que determine si el asistente está activo

    if (!asistenteActivo) {
        chatWindow.classList.add('asistente-inactivo');
        mostrarMensajeAsistente("El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación.");
    }

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
    }
}