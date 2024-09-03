// Espera a que el DOM esté completamente cargado antes de ejecutar las funciones
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();       // Carga la información del usuario
    loadModules();        // Carga los módulos del sistema
    loadTasks();          // Carga las tareas pendientes
    loadNotifications();  // Carga las notificaciones
    initializeCharts();   // Inicializa los gráficos
    initializeCalendar(); // Inicializa el calendario
    initializeAsistente();// Inicializa el asistente virtual
    window.addEventListener('resize', resizeCharts); // Ajusta los gráficos al redimensionar la ventana

        // Agrega event listeners para mostrar/ocultar gráficos
        ['line', 'bar', 'pie'].forEach(type => {
            const toggleButton = document.getElementById(`toggle-${type}-chart`);
            if (toggleButton) {
                toggleButton.addEventListener('click', () => toggleChartVisibility(`${type}-chart`));
            }
        });
    });
    
    // Nueva función para inicializar los manejadores de submódulos
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
    
    // Nueva función para manejar el clic en submódulos
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
    
    // ... (resto de las funciones existentes sin cambios)
    
    // Modificar la función loadSubmodules para usar handleSubmoduleClick
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

// Carga la información del usuario desde la API
function loadUserInfo() {
    fetch('/api/usuario')
        .then(response => response.json())
        .then(usuario => {
            document.getElementById('user-name').textContent = usuario.nombre;  // Muestra el nombre del usuario
            document.getElementById('user-id').textContent = usuario.id;        // Muestra el ID del usuario
        })
        .catch(error => console.error('Error loading user info:', error)); // Maneja errores en la carga de la información del usuario
}

// Carga los módulos del sistema desde la API
function loadModules() {
    fetch('/api/modulos')
        .then(response => response.json())
        .then(modulos => {
            const moduleContainer = document.getElementById('module-container');
            moduleContainer.innerHTML = ''; // Limpia el contenedor de módulos
            const colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#FFC0CB", "#98D8C8", "#F06292", "#AED581", "#FFD54F", "#800000", "#4DB6AC", "#075e56"];
            modulos.forEach((modulo, index) => {
                const moduleDiv = createModuleElement(modulo, colors[index % colors.length]); // Crea y agrega cada módulo
                moduleContainer.appendChild(moduleDiv);
            });
        })
        .catch(error => console.error('Error loading modules:', error)); // Maneja errores en la carga de los módulos
}

// Crea un elemento HTML para un módulo
function createModuleElement(modulo, color) {
    const moduleDiv = document.createElement('div');
    moduleDiv.className = 'module-wrapper';
    
    const button = createButton(modulo, 'rectangular-button', color); // Crea el botón para el módulo
    button.onclick = () => toggleSubmodules(modulo, moduleDiv); // Añade el evento para alternar la visibilidad de submódulos
    
    const submoduleContainer = document.createElement('div');
    submoduleContainer.className = 'submodule-container'; // Contenedor para los submódulos
    
    moduleDiv.appendChild(button);
    moduleDiv.appendChild(submoduleContainer);
    return moduleDiv;
}

// Crea un botón genérico
function createButton(text, className, color) {
    const button = document.createElement('button');
    button.textContent = text; // Texto del botón
    button.className = className; // Clase CSS del botón
    if (color) button.style.backgroundColor = color; // Color de fondo del botón, si se proporciona
    if (className === 'submodule-button') {
        button.style.width = 'auto'; // Ajusta el ancho para botones de submódulos
    }
    return button;
}

// Alterna la visibilidad de los submódulos
function toggleSubmodules(moduleName, moduleDiv) {
    const submoduleContainer = moduleDiv.querySelector('.submodule-container');
    const moduleButton = moduleDiv.querySelector('.rectangular-button');
    const isOpen = submoduleContainer.style.display === 'block'; // Verifica si los submódulos están visibles

    document.querySelectorAll('.submodule-container').forEach(container => {
        if (container !== submoduleContainer) {
            container.style.display = 'none'; // Oculta todos los submódulos menos el seleccionado
        }
    });
    document.querySelectorAll('.rectangular-button').forEach(btn => {
        if (btn !== moduleButton) {
            btn.classList.remove('active'); // Desactiva todos los botones menos el seleccionado
        }
    });

    if (!isOpen) {
        moduleButton.classList.add('active'); // Activa el botón seleccionado
        submoduleContainer.style.display = 'block'; // Muestra los submódulos del módulo seleccionado
        loadSubmodules(moduleName, submoduleContainer); // Carga los submódulos si es necesario
    } else {
        moduleButton.classList.remove('active'); // Desactiva el botón
        submoduleContainer.style.display = 'none'; // Oculta los submódulos
    }
}

// Carga los submódulos de un módulo específico
function loadSubmodules(moduleName, submoduleContainer) {
    if (submoduleContainer.children.length === 0) {
        fetch(`/api/submodulos/${moduleName}`)
            .then(response => response.json())
            .then(submodulos => {
                submoduleContainer.innerHTML = ''; // Limpia el contenedor de submódulos
                submodulos.forEach(submodulo => {
                    const button = createButton(submodulo, 'submodule-button'); // Crea botones para cada submódulo
                    button.onclick = () => loadSubmoduleContent(moduleName, submodulo); // Evento para cargar el contenido del submódulo
                    submoduleContainer.appendChild(button); // Agrega el botón al contenedor
                });
            })
            .catch(error => console.error('Error loading submodules:', error)); // Maneja errores en la carga de submódulos
    }
}

// Carga el contenido de un submódulo específico (función a implementar)
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
            ).join(''); // Muestra la lista de tareas pendientes
        })
        .catch(error => console.error('Error loading tasks:', error)); // Maneja errores en la carga de tareas
}

// Carga las notificaciones desde la API
function loadNotifications() {
    fetch('/api/notificaciones')
        .then(response => response.json())
        .then(notificaciones => {
            const notificationList = document.getElementById('notification-list');
            notificationList.innerHTML = notificaciones.map(notificacion => 
                `<li class="${notificacion.tipo}">${notificacion.mensaje}</li>`
            ).join(''); // Muestra la lista de notificaciones
        })
        .catch(error => console.error('Error loading notifications:', error)); // Maneja errores en la carga de notificaciones
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
            createLineChart(datos.ventas);            // Crea un gráfico de líneas para ventas
            createBarChart(datos.ingresos_vs_gastos); // Crea un gráfico de barras para ingresos vs gastos
            createPieChart(datos.distribucion);       // Crea un gráfico circular para distribución
        })
        .catch(error => console.error('Error initializing charts:', error)); // Maneja errores en la inicialización de gráficos

    // Agrega event listeners para mostrar/ocultar gráficos
    ['line', 'bar', 'pie'].forEach(type => {
        const toggleButton = document.getElementById(`toggle-${type}-chart`);
        if (toggleButton) {
            toggleButton.addEventListener('click', () => toggleChartVisibility(`${type}-chart`)); // Alterna la visibilidad del gráfico
        }
    });
}

// Crea el gráfico de líneas
function createLineChart(data) {
    const ctx = document.getElementById('line-chart').getContext('2d');
    lineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels, // Etiquetas para el eje X
            datasets: [{
                label: 'Ventas',
                data: data.values, // Datos para las ventas
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

function handleSubmoduleClick(moduleName, submoduleName) {
    console.log(`Clicked on ${submoduleName} of ${moduleName}`);
    if (moduleName === 'Banco' && submoduleName === 'Bancos') {
        window.location.href = '/Bancos';
    } else {
        // Manejar otros submódulos aquí
        console.log('Otro submódulo clickeado');
    }
}

// Asegúrate de que esta función se llame cuando se hace clic en un submódulo
document.addEventListener('DOMContentLoaded', function() {
    const submodules = document.querySelectorAll('.submodule-button');
    submodules.forEach(submodule => {
        submodule.addEventListener('click', function() {
            const moduleName = this.closest('.module-wrapper').querySelector('.rectangular-button').textContent;
            const submoduleName = this.textContent;
            handleSubmoduleClick(moduleName, submoduleName);
        });
    });
});

// Crea el gráfico de barras
function createBarChart(data) {
    const ctx = document.getElementById('bar-chart').getContext('2d');
    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels, // Etiquetas para el eje X
            datasets: [{
                label: 'Ingresos',
                data: data.ingresos, // Datos para los ingresos
                backgroundColor: '#4ECDC4'
            }, {
                label: 'Gastos',
                data: data.gastos, // Datos para los gastos
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
            labels: data.labels, // Etiquetas para el gráfico
            datasets: [{
                data: data.values, // Valores para el gráfico circular
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
    if (lineChart) lineChart.resize(); // Redimensiona el gráfico de líneas
    if (barChart) barChart.resize();   // Redimensiona el gráfico de barras
    if (pieChart) pieChart.resize();   // Redimensiona el gráfico circular
}

// Alterna la visibilidad de los gráficos
function toggleChartVisibility(chartId) {
    const chartContainer = document.getElementById(chartId);
    chartContainer.style.display = chartContainer.style.display === 'none' ? 'block' : 'none'; // Muestra u oculta el gráfico
}

// Inicializa el calendario utilizando una librería (suponiendo que uses algo como FullCalendar)
function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: '/api/eventos', // Carga los eventos desde la API
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        }
    });

    // Modificar el tamaño y la forma del calendario con JavaScript
    calendarEl.style.width = '60%'; /* Ajusta el ancho del calendario (más pequeño) */
    calendarEl.style.maxWidth = '600px'; /* Limita el ancho máximo del calendario */
    calendarEl.style.height = '400px'; /* Cambia la altura del calendario (más pequeño) */
    calendarEl.style.borderRadius = '8px'; /* Ajusta los bordes redondeados */
    calendarEl.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)'; /* Cambia la sombra */

    calendar.render(); // Renderiza el calendario
}



// Inicializa el asistente virtual
function initializeAsistente() {
    document.getElementById('asistente-button').addEventListener('click', () => {
        alert('Activando Asistente Virtual'); // Muestra una alerta (puedes personalizar esto)
    });
}
