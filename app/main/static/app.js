const socket = io("/game", {query: {game: game_slug}});

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