function init() {
    set_event({"player_joined": player});
    document.getElementById("button_start_game").addEventListener("click", function() {
        var value = document.querySelector('input[name=board]:checked').value;
        set_event({"game_started": value});
    });
    window.addEventListener("unload", unload);
    get_event();
}

function unload() { set_event({"player_left": player}) }

function get_event() {
    fetch('/get_event', {
          method: 'POST',
          headers: {'Content-Type': 'application/json;charset=utf-8'},
          body: JSON.stringify({game_id: game_id})})
    .then(response => response.json())
    .then(function(result) {
        if (result["is-started"]) {
            window.removeEventListener("unload", unload);
            location.reload();
        } else {
            print_players(result["players"]);
        }
        get_event();
    });
}

function set_event(dict) {
    dict["game_id"] = game_id;
    fetch('/set_event', {method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify(dict),
    keepalive: true});
}

function print_players(players) {
    var i;
    var html = "";
    for (i = 0; i < players.length; i++){
        var str = "<li>".concat(players[i][0], "</li>");
        html = html.concat(str);
    }
    document.getElementById("player_section").innerHTML = html;
}

window.addEventListener("load", function(event) {init();});