const socket = io("/lobby", {
    query: {
        game: game_slug
    }
});

socket.on('connect', function() {
    console.log("Socket connected.");
});

document.addEventListener("DOMContentLoaded", function(event) {
    console.log("DOM fully loaded and parsed");

    const loginForm = document.getElementById("LoginForm")
    const adminForm = document.getElementById("AdminForm")

    loginForm.addEventListener("submit", function (e) {
        e.preventDefault();
        send_form("login", this);
    });

    adminForm.addEventListener("submit", function (e) {
        e.preventDefault();
        send_form("admin", this);
    });
});

function send_form(event, formElement) {
    let object = {};
    let formData = new FormData(formElement)
    formData.forEach((value, key) => object[key] = value);
    socket.emit(event, object, data => {
        if (!data) {
            console.error("Error sending message.")
        }
        else {
            if (!data.success) {
                console.error(data.status_code + " - " + data.message);
            }
        }
    });
}

socket.on('players', function(data) {
    const players = document.getElementById("players");
    while (players.firstChild) {players.removeChild(players.firstChild);}
    data.forEach(player => {
        let a = document.createElement("a");
        a.innerText = player[1];
        let li = document.createElement("li");
        li.id = player[0];
        li.appendChild(a);
        players.appendChild(li);
    });
})

socket.on('game started', function() {
    window.location.replace("/game/" + game_slug);
})