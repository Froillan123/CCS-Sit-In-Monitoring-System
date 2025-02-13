document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('.form__input');

    inputs.forEach(input => {
        input.value = '';
        let parent = input.parentNode.parentNode;
        parent.classList.remove("focus");
    });

    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((flashMessage) => {
        setTimeout(() => {
            flashMessage.classList.add('fade-out');
        }, 2500);
        flashMessage.addEventListener('animationend', () => {
            flashMessage.remove();
        });
    });

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

const sideMenu = document.querySelector('aside');
const menuBtn = document.getElementById('menu-btn');
const closeBtn = document.getElementById('close-btn');



menuBtn.addEventListener('click', () => {
    sideMenu.style.display = 'block';
});

closeBtn.addEventListener('click', () => {
    sideMenu.style.display = 'none';
});


const darkMode = document.querySelector('.dark-mode');

function applyDarkModePreference() {
    const isDarkMode = localStorage.getItem('darkMode') === 'enabled';

    if (isDarkMode) {
        document.body.classList.add('dark-mode-variables');
        darkMode.querySelector('span:nth-child(1)').classList.remove('active');
        darkMode.querySelector('span:nth-child(2)').classList.add('active');
    } else {
        document.body.classList.remove('dark-mode-variables');
        darkMode.querySelector('span:nth-child(1)').classList.add('active');
        darkMode.querySelector('span:nth-child(2)').classList.remove('active');
    }
}

applyDarkModePreference();

darkMode.addEventListener('click', () => {
    const isDarkMode = document.body.classList.toggle('dark-mode-variables');

    if (isDarkMode) {
        localStorage.setItem('darkMode', 'enabled');
        darkMode.querySelector('span:nth-child(1)').classList.remove('active');
        darkMode.querySelector('span:nth-child(2)').classList.add('active');
    } else {
        localStorage.setItem('darkMode', 'disabled');
        darkMode.querySelector('span:nth-child(1)').classList.add('active');
        darkMode.querySelector('span:nth-child(2)').classList.remove('active');
    }
});

function updateUserCount() {
    fetch('/get_user_count')
        .then(response => response.json())
        .then(data => {
            document.querySelector('.info h1').textContent = data.student_count;
        });
}

setInterval(updateUserCount, 10000);
updateUserCount();

const eventSource = new EventSource("/sse/active_users");

eventSource.onmessage = function (event) {
    const activeUsersCount = JSON.parse(event.data);
    const activeUsersCountElement = document.getElementById('active-users-count');

    if (activeUsersCountElement) {
        activeUsersCountElement.textContent = activeUsersCount;
    }

    const activeUsersListElement = document.getElementById('active-users-list');
    if (activeUsersListElement) {
        activeUsersListElement.innerHTML = '';
    }
};

eventSource.onerror = function () {
    eventSource.close();
};
