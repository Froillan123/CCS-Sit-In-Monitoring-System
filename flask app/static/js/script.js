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

    // Password visibility toggle for Login
    const passwordAccess = (loginPass, loginEye) => {
        const input = document.getElementById(loginPass),
            iconEye = document.getElementById(loginEye);

        iconEye.addEventListener('click', () => {
            // Change password to text or password
            input.type = input.type === 'password' ? 'text' : 'password';

            // Icon change
            iconEye.classList.toggle('ri-eye-fill');
            iconEye.classList.toggle('ri-eye-off-fill');
        });
    }
    passwordAccess('password', 'loginPassword'); // For Login
});


   // Function to update the title based on the width
   function updateTitle() {
    const titleElement = document.querySelector('.login__title');
    if (window.innerWidth <= 410) {
        titleElement.textContent = 'Login';  // Set the text to 'Login' if width is 410px or less
    } else {
        titleElement.textContent = 'Log in to your account.';  // Default text
    }
}

window.onload = updateTitle;

window.onresize = updateTitle;