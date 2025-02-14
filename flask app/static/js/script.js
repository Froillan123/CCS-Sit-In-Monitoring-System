document.addEventListener('DOMContentLoaded', () => {
    // Handling Flash Messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((flashMessage) => {
        setTimeout(() => {
            flashMessage.classList.add('fade-out');
        }, 2500);
        flashMessage.addEventListener('animationend', () => {
            flashMessage.remove();
        });
    });

    // Password visibility toggle function
    const passwordAccess = (inputId, eyeId) => {
        const input = document.getElementById(inputId);
        const iconEye = document.getElementById(eyeId);

        if (input && iconEye) {
            iconEye.addEventListener('click', () => {
                input.type = input.type === 'password' ? 'text' : 'password';
                iconEye.classList.toggle('ri-eye-fill');
                iconEye.classList.toggle('ri-eye-off-fill');
            });
        }
    };

    passwordAccess('password', 'loginPasswordEye');
    passwordAccess('password', 'passwordEye');
    passwordAccess('repeat_password', 'repeatPasswordEye');

    // Function to update title on small screens
    const updateTitle = () => {
        const titleElement = document.querySelector('.login__title');
        if (titleElement) {
            titleElement.textContent = window.innerWidth <= 410 ? 'Login' : 'Log in to your account.';
        }
    };

    window.onload = updateTitle;
    window.onresize = updateTitle;

    // Password validation
    const passwordInput = document.getElementById('password');
    const repeatPasswordInput = document.getElementById('repeat_password');

    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            validatePassword(passwordInput);
            if (repeatPasswordInput) {
                validateRepeatPassword(repeatPasswordInput, passwordInput);
            }
        });
    }

    if (repeatPasswordInput) {
        repeatPasswordInput.addEventListener('input', () => {
            validateRepeatPassword(repeatPasswordInput, passwordInput);
        });
    }
});

// Form validation logic
const form = document.querySelector('.register');

form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (validateInputs()) {
        form.submit();
    } else {
        alert('Please fill out all fields correctly before submitting.');
    }
});

const setError = (element, message) => {
    const inputControl = element.closest('.input-box');
    let errorDisplay = inputControl.querySelector('.error-message');

    if (!errorDisplay) {
        errorDisplay = document.createElement('div');
        errorDisplay.classList.add('error-message');
        inputControl.appendChild(errorDisplay);
    }

    errorDisplay.innerText = message;
    inputControl.classList.add('error');
    inputControl.classList.remove('success');
};

const setSuccess = (element) => {
    const inputControl = element.closest('.input-box');
    const errorDisplay = inputControl.querySelector('.error-message');

    if (errorDisplay) {
        errorDisplay.remove();
    }

    inputControl.classList.remove('error');
    inputControl.classList.add('success');
};

const isValidEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
};

// Validate password
const validatePassword = (passwordInput) => {
    const value = passwordInput.value.trim();

    if (value.length < 8) {
        setError(passwordInput, 'Password must be at least 8 characters');
        return false;
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
        setError(passwordInput, 'Password must contain at least one special character');
        return false;
    }

    setSuccess(passwordInput);
    return true;
};

const validateRepeatPassword = (repeatPasswordInput, passwordInput) => {
    if (repeatPasswordInput.value.trim() !== passwordInput.value.trim()) {
        setError(repeatPasswordInput, 'Passwords do not match');
        return false;
    }

    setSuccess(repeatPasswordInput);
    return true;
};

const validateInputs = () => {
    let isValid = true;

    const emailInput = form.querySelector('input[name="email"]');
    const passwordInput = form.querySelector('input[name="password"]');
    const repeatPasswordInput = form.querySelector('input[name="repeat_password"]');

    if (!emailInput.value.trim()) {
        setError(emailInput, 'Email is required');
        isValid = false;
    } else if (!isValidEmail(emailInput.value)) {
        setError(emailInput, 'Provide a valid email address');
        isValid = false;
    } else {
        setSuccess(emailInput);
    }

    if (!passwordInput.value.trim() || !validatePassword(passwordInput)) {
        isValid = false;
    }

    if (!validateRepeatPassword(repeatPasswordInput, passwordInput)) {
        isValid = false;
    }

    return isValid;
};



