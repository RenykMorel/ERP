document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#form-login, #form-registro');
    const errorDiv = document.getElementById('auth-error');
    const passwordToggle = document.querySelector('.password-toggle');
    const numpadButtons = document.querySelectorAll('.numpad-btn');

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);

            fetch(form.action, {
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
                    showError(data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('Ocurrió un error durante la autenticación. Por favor, inténtalo de nuevo.');
            });
        });
    }

    if (passwordToggle) {
        passwordToggle.addEventListener('click', function() {
            const passwordInput = this.previousElementSibling;
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.textContent = '🔒';
            } else {
                passwordInput.type = 'password';
                this.textContent = '👁️';
            }
        });
    }

    if (numpadButtons.length > 0) {
        numpadButtons.forEach(button => {
            button.addEventListener('click', function() {
                const activeInput = document.activeElement;
                if (activeInput.tagName === 'INPUT' && activeInput.type !== 'submit') {
                    activeInput.value += this.textContent;
                }
            });
        });
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
});