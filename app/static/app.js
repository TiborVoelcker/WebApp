const socket = io.connect();

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
});

socket.on('player left', function(data) {
    if (document.getElementById(data.id)) {
        var player = document.getElementById(data.id);
        player.parentNode.removeChild(player);
    }
});

socket.on("error", function(data) {
   console.log(data)
});