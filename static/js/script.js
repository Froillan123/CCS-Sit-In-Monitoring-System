document.addEventListener('DOMContentLoaded', () => {
   
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((flashMessage) => {
        setTimeout(() => {
            flashMessage.classList.add('fade-out');
        }, 2500);
        flashMessage.addEventListener('animationend', () => {
            flashMessage.remove();
        });
    });

});


document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('.user-details .input-box input');

    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.borderColor = '#2196f3'; // When the field is focused
        });

        input.addEventListener('blur', function() {
            // If the field is empty, reset to default border color
            if (this.value === '') {
                this.style.borderColor = '#ccc';
            } else {
                this.style.borderColor = '#2196f3'; // Keep blue if not empty
            }
        });
    });
});

