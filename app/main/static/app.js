const socket = io({query: {game: game_slug}});

document.addEventListener("DOMContentLoaded", function(event) {
    console.log("DOM fully loaded and parsed");
    socket.connect();

    document.getElementById("start_game").addEventListener('click', function (e) {
        socket.emit("start game", (flag, message) => {
            if (flag) {document.getElementById("pre_game").hidden = true}
            else {console.log(message);}
        })
    });
})

socket.on('player joined', function(data) {
    if (!document.getElementById(data.id)) {
        var players = document.getElementById("players");
        var li = document.createElement("li");
        var a = document.createElement("a");
        li.id = data.id;
        a.textContent = data.name;
        li.appendChild(a);
        players.appendChild(li);
    }
})

socket.on('player left', function(data) {
    if (document.getElementById(data.id)) {
        var player = document.getElementById(data.id);
        player.parentNode.removeChild(player);
    }
})

socket.on('new president', function (data) {
    var player = document.getElementById(data.id);
    player.classList.add("president")
})

socket.on('nominate chancellor', function (data) {
    document.getElementById("nomination").hidden = false;
})

socket.on("error", function(data) {
   console.log(data)
})

//ToDo: implement basic featues