// dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard JavaScript loaded');
    // Aquí puedes añadir la lógica específica del dashboard
    initializeCharts();
    initializeCalendar();
});

function initializeCharts() {
    // Lógica para inicializar los gráficos
}

function initializeCalendar() {
    var calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            events: '/api/eventos'
        });
        calendar.render();
    }
}