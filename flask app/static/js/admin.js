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

function updateUserCount() {
    fetch('/get_user_count')
    .then(response => response.json())
    .then(data => {
        document.querySelector('.info h1').textContent = data.student_count;
    });
}

// Refresh count every 10 seconds
setInterval(updateUserCount, 10000);
updateUserCount();


const socket = io.connect(window.location.origin, {
    transports: ["websocket", "polling"]
});

socket.on("connect", function () {
    console.log("Connected to WebSocket!");
});

socket.on("update_active_users", function (activeUsers) {
    console.log("Active users received:", activeUsers);
    
    let activeUsersCountElement = document.querySelector("#activeUsersCount");
    if (activeUsersCountElement) {
        activeUsersCountElement.textContent = activeUsers.length;
    } else {
        console.error("Element #activeUsersCount not found!");
    }
});

socket.on("user_login", function (username) {
    console.log("User logged in:", username);
    updateActiveUsers();
});

socket.on("user_logout", function (username) {
    console.log("User logged out:", username);
    updateActiveUsers();
});

function updateActiveUsers() {
    fetch("/fetch_active_users")
        .then(response => response.json())
        .then(data => {
            let activeUsersCountElement = document.querySelector("#activeUsersCount");
            if (activeUsersCountElement) {
                activeUsersCountElement.textContent = data.active_users;
            } else {
                console.error("Element #activeUsersCount not found!");
            }
        });
}

document.addEventListener("DOMContentLoaded", function () {
    updateActiveUsers();
});