function init() {
    document.getElementById("button_leave_game").addEventListener("click", function() {
        set_event({"player_left": player});
        window.location.replace("/");
    });
    window.onbeforeunload = function(e) {
        return 'Are you sure you want to leave?';};

    get_event();
    set_event({"reload": true});
}

function get_event() {
    fetch('/get_event', {
          method: 'POST',
          headers: {'Content-Type': 'application/json;charset=utf-8'},
          body: JSON.stringify({game_id: game_id})})
    .then(response => response.json())
    .then(gamestate => get_roles(gamestate))
    .then(gamestate => {
        print_players(gamestate, "player_list");
        print_board(gamestate);

        if (gamestate["players"][gamestate["current_president"]][0] == player[0]
        && gamestate["players"][gamestate["current_president"]][1] == player[1]) {
            choose_chancellor(gamestate);
        }
        if (gamestate["current_chancellor"]) {
            if (gamestate["players"][gamestate["current_chancellor"]][0] == player[0]
            && gamestate["players"][gamestate["current_chancellor"]][1] == player[1]) {
                choose_policies();
            }
        }

        get_event();
    })
    .catch(error => {
        console.log(error);
        get_event();
    })
}

function set_event(dict) {
    dict["game_id"] = game_id;
    return fetch('/set_event', {method: 'POST',
    headers: {'Content-Type': 'application/json;charset=utf-8'},
    body: JSON.stringify(dict),
    keepalive: true})
    .then(response => response.json())
    .then(result => {if(result["success"]) {return true}else{throw false}});
}

function print_players(gamestate, id) {
    var i;
    var html = "";
    var list = document.getElementById(id);
    list.textContent = '';
    for (i = 0; i < gamestate["players"].length; i++){
        var li = document.createElement("li");
        if (gamestate["roles"][i] == 1) {li.style = "color:#FF5733"}
        else if (gamestate["roles"][i] == 2) {li.style = "color:#C63E21"}
        var a = document.createElement("a");
        a.href = "#";
        a.textContent = gamestate["players"][i][0];
        a.id = "player".concat(i);
        li.appendChild(a);
        list.appendChild(li);
    }
}

function print_board(gamestate) {
    var pres = document.getElementById("player".concat(gamestate["current_president"]));
    var pres_fig = document.createElement("img");
    pres_fig.src = '/static/images/Current_President.png'
    pres_fig.style = "height:100px"
    pres.appendChild(pres_fig)
}


function get_roles(gamestate) {
    return fetch('/secure', {
          method: 'POST',
          headers: {'Content-Type': 'application/json;charset=utf-8'},
          body: JSON.stringify({game_id: game_id, role_all: true})})
    .then(response => response.json())
    .then(function(result) {
        gamestate["roles"] = result["roles"];
        return gamestate;
    });
}

function policies(dict) {
    dict["game_id"] = game_id
    return fetch('/secure', {
          method: 'POST',
          headers: {'Content-Type': 'application/json;charset=utf-8'},
          body: JSON.stringify(dict)})
    .then(response => response.json())
}


function choose_chancellor(gamestate) {
    document.addEventListener("click", chancellor_chosen);
    document.getElementById("main_game").classList.value = "content_blurred";
    document.body.appendChild(popup_choose_chancellor)
    print_players(gamestate, "popup_player_list");
}

function chancellor_chosen(event) {
    var target = event.target;
    set_event({chancellor_chosen: target.id})
    .then(function() {
        document.getElementById("main_game").classList.value = "content";
        document.body.removeChild(docuument.getElementById("popup_choose_chancellor"));
        console.log("removed")
    }).catch(err => console.log("You can't choose yourself!"))
    .then(policies({"get_policies_president": true})
    .then(result => choose_policies(result["policies"])));
}

function choose_policies(policies){
    document.addEventListener("click", policies_chosen)
    document.getElementById("main_game").classList.value = "content_blurred";
    document.getElementById("select_policies").classList.value = "popup_active";
    var i;
    for (i=0; i<policies.length; i++) {
        var li = document.createElement("li");
        li.id = "policy".concat(i);
        if (policies[i] == 0) {li.textContent = "liberal Policy"}
        if (policies[i] == 1) {li.textContent = "fascist Policy"}
        document.getElementById("choose_policies_list").appendChild(li)
    }
}

function policies_chosen(event){
    var target = event.target
    console.log(target)
}

window.addEventListener("load", function(event) {init();});
var popup_choose_chancellor = document.createElement("div");
popup_choose_chancellor.id = "popup_choose_chancellor";
popup_choose_chancellor.className = "popup";
popup_choose_chancellor.innerHTML = `<section id="popup_player_section">
                                        <ul id="popup_player_list"/>
                                    </section>`;