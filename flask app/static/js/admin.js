document.addEventListener('DOMContentLoaded', () => {
    // 1. Prevent form fields from retaining values when pressing the back button
    const inputs = document.querySelectorAll('.form__input');
    
    // Clear values and reset form styles when the page loads
    inputs.forEach(input => {
        input.value = ''; // Clear the input field value
        let parent = input.parentNode.parentNode;
        parent.classList.remove("focus"); // Ensure the label isn't floating
    });

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

    // Focus and blur handlers for form inputs
    function addfocus() {
        let parent = this.parentNode.parentNode;
        parent.classList.add("focus");
    }

    function remfocus() {
        let parent = this.parentNode.parentNode;
        if (this.value == "") {
            parent.classList.remove("focus");
        }
    }

    inputs.forEach(input => {
        input.addEventListener("focus", addfocus);
        input.addEventListener("blur", remfocus);
    });
});

// Disable Right Click (Context Menu)
document.addEventListener('contextmenu', (e) => {
    e.preventDefault(); // Prevent right-click menu
});

// Disable F12/DevTools Shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
        e.preventDefault(); // Disable DevTools shortcuts
    }
});




const sideMenu = document.querySelector('aside');
const menuBtn = document.getElementById('menu-btn');
const closeBtn = document.getElementById('close-btn');

const darkMode = document.querySelector('.dark-mode');

menuBtn.addEventListener('click', () => {
    sideMenu.style.display = 'block';
});

closeBtn.addEventListener('click', () => {
    sideMenu.style.display = 'none';
});

darkMode.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode-variables');
    darkMode.querySelector('span:nth-child(1)').classList.toggle('active');
    darkMode.querySelector('span:nth-child(2)').classList.toggle('active');
})