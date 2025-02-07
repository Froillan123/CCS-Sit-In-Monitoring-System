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
                // Toggle password visibility
                input.type = input.type === 'password' ? 'text' : 'password';

                // Toggle eye icon
                iconEye.classList.toggle('ri-eye-fill');
                iconEye.classList.toggle('ri-eye-off-fill');
            });
        }
    };

    // Apply password visibility toggle
    passwordAccess('password', 'loginPassword'); // For Login
    passwordAccess('registerPassword', 'registerEye'); // For Registration

    // Function to update the title based on window width
    const updateTitle = () => {
        const titleElement = document.querySelector('.login__title');
        if (titleElement) {
            titleElement.textContent = window.innerWidth <= 410 ? 'Login' : 'Log in to your account.';
        }
    };

    // Run updateTitle on load and on window resize
    window.onload = updateTitle;
    window.onresize = updateTitle;

});

const form = document.querySelector('.register');
const inputs = form.querySelectorAll('input, select');

form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (validateInputs()) {
        form.submit(); // Submit only if validation passes
    } else {
        alert('Please fill out all fields correctly before submitting.');
    }
});

const setError = (element, message) => {
    const inputControl = element.parentElement;
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
    const inputControl = element.parentElement;
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

const validateInputs = () => {
    let isValid = true;

    inputs.forEach((input) => {
        const value = input.value.trim();
        const name = input.name;

        if (value === '') {
            setError(input, `${input.previousElementSibling.innerText} is required`);
            isValid = false;
        } else {
            setSuccess(input);
        }

        if (name === 'email' && value !== '' && !isValidEmail(value)) {
            setError(input, 'Provide a valid email address');
            isValid = false;
        }

        if (name === 'password' && value !== '' && value.length < 8) {
            setError(input, 'Password must be at least 8 characters');
            isValid = false;
        }
    });

    // Validate password and repeat password match
    const password = form.querySelector('input[name="password"]').value.trim();
    const repeatPassword = form.querySelector('input[name="repeat_password"]').value.trim();

    if (password !== repeatPassword) {
        setError(form.querySelector('input[name="repeat_password"]'), 'Passwords do not match');
        isValid = false;
    }

    return isValid;
};

// Add focus and blur event listeners to inputs
inputs.forEach((input) => {
    input.addEventListener('focus', () => {
        const inputControl = input.parentElement;
        inputControl.classList.remove('error'); // Reset to default (main) color on focus
    });

    input.addEventListener('blur', () => {
        const value = input.value.trim();
        if (value === '') {
            setError(input, `${input.previousElementSibling.innerText} is required`);
        } else {
            setSuccess(input);
        }
    });
});