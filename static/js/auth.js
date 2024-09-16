document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#form-login, #form-registro');
    const errorDiv = document.getElementById('auth-error');
    const passwordToggles = document.querySelectorAll('.password-toggle');
    const numpadButtons = document.querySelectorAll('.numpad-btn');
    const forgotPasswordLink = document.getElementById('forgot-password-link');

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', togglePasswordVisibility);
    });

    if (numpadButtons.length > 0) {
        numpadButtons.forEach(button => {
            button.addEventListener('click', handleNumpadInput);
        });
    }

    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', handleForgotPassword);
    }

    function handleFormSubmit(e) {
        e.preventDefault();
        const formData = new FormData(e.target);

        fetch(e.target.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/';
            } else if (data.allow_password_reset) {
                showPasswordResetOption(data.nombre_usuario);
            } else {
                showError(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ocurrió un error durante la autenticación. Por favor, inténtalo de nuevo.');
        });
    }

    function togglePasswordVisibility() {
        const passwordInput = this.previousElementSibling;
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        this.textContent = type === 'password' ? '👁️' : '🔒';
    }

    function handleNumpadInput() {
        const activeInput = document.activeElement;
        if (activeInput.tagName === 'INPUT' && activeInput.type !== 'submit') {
            activeInput.value += this.textContent;
        }
    }

    function handleForgotPassword(e) {
        e.preventDefault();
        const emailInput = document.querySelector('input[type="email"]');
        const email = emailInput ? emailInput.value : '';

        if (!email) {
            showError('Por favor, ingresa tu correo electrónico antes de solicitar un restablecimiento de contraseña.');
            return;
        }

        fetch('/request_password_reset', {
            method: 'POST',
            body: JSON.stringify({ email: email }),
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
            } else {
                showError(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ocurrió un error al solicitar el restablecimiento de contraseña. Por favor, inténtalo de nuevo.');
        });
    }

    function showPasswordResetOption(nombre_usuario) {
        const container = form.parentElement;
        container.innerHTML = `
            <h2>Cambiar Contraseña</h2>
            <form id="form-reset-password">
                <input type="hidden" name="nombre_usuario" value="${nombre_usuario}">
                <div class="input-group password-group">
                    <input type="password" name="new_password" placeholder="Nueva contraseña" required>
                    <button type="button" class="password-toggle">👁️</button>
                </div>
                <div class="input-group password-group">
                    <input type="password" name="confirm_password" placeholder="Confirmar nueva contraseña" required>
                    <button type="button" class="password-toggle">👁️</button>
                </div>
                <button type="submit">Cambiar Contraseña</button>
            </form>
        `;
        const resetForm = document.getElementById('form-reset-password');
        resetForm.addEventListener('submit', handleResetPassword);
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            toggle.addEventListener('click', togglePasswordVisibility);
        });
    }

    function handleResetPassword(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
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
                showMessage('Contraseña cambiada exitosamente. Por favor, inicia sesión con tu nueva contraseña.', 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            } else {
                showError(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Ocurrió un error al cambiar la contraseña. Por favor, inténtalo de nuevo.');
        });
    }

    function showError(message) {
        showMessage(message, 'error');
    }

    function showMessage(message, type) {
        const messageDiv = errorDiv || document.createElement('div');
        messageDiv.textContent = message;
        messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
        messageDiv.style.display = 'block';
        if (!errorDiv) {
            form.parentElement.insertBefore(messageDiv, form);
        }
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
});