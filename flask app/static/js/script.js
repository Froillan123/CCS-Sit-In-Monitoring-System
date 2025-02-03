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
