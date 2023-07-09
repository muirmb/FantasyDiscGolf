function setup() {
    document.getElementById("searchButton").addEventListener("click", search);
    document.getElementById('sortByRating').addEventListener("click", () => {sort("rating");});
    document.getElementById('sortByPdgaNum').addEventListener("click", () => {sort("pdga-num")});
    document.getElementById('sortByName').addEventListener("click", () => {sort("name")});
}

function sort(attribute) {
    console.log("Sending POST request for sort");
    var leagueName = "";
    if(document.getElementById("navbarSupportedContent").contains(document.getElementById("leagueDropdown")))
        leagueName = document.getElementById("leagueNameDropdown").innerText;
        fetch("/sortPlayers", {
            method: "post",
            headers: { "Content-type": "application/json; charset=UTF-8" },
            body: JSON.stringify({
                attr: attribute,
                league: leagueName
            })
        })
        .then((response) => {
            return response.json();
        })
        .then((result) => {
            updatePlayers(result);
        })
        .catch(() => {
            console.log("Error posting new items!");
        });
}

function search() {
    console.log("Sending POST request for search");
    const searchString = document.getElementById("searchString").value;
    var whichPlayers = "";
    var leagueName = "";
    if(document.getElementById("navbarSupportedContent").contains(document.getElementById("leagueDropdown"))) {
        whichPlayers = "av";
        leagueName = document.getElementById("leagueNameDropdown").innerText;
    }
    else 
        whichPlayers = "all";
    
    fetch("/search", {
        method: "post",
        headers: { "Content-type": "application/json; charset=UTF-8" },
        body: JSON.stringify({
            string: searchString,
            selection: whichPlayers,
            league: leagueName
        })
    })
    .then((response) => {
        return response.json();
    })
    .then((result) => {
        updatePlayers(result);
    })
    .catch(() => {
        console.log("Error posting new items!");
    });
}

function updatePlayers(result) {
    playerArea = document.getElementById("playerArea");
    num = playerArea.children.length;
    for (var i = 0; i < num; i++) {
        playerArea.removeChild(playerArea.firstElementChild);
    }

    start = 0;
    if(document.getElementById("navbarSupportedContent").contains(document.getElementById("leagueDropdown")))
        start = 1;
    for (var i = start; i < result.length; i++) {
        rect = document.createElement("a");
        image = document.createElement("img");
        player_name = document.createElement("h5");
        rect.href = "#";
        rect.setAttribute("class", "list-group-item list-group-item-action");
        rect.id = result[i].pdga_number;

        form_area = document.createElement("div");
        form_area.className = "add-button-area";

        if(document.getElementById("navbarSupportedContent").contains(document.getElementById("leagueDropdown")) && ((result[i].division == "MPO" && result[0].mpoPlayers < 5) || (result[i].division == "FPO" && result[0].fpoPlayers < 3))) {
            form = document.createElement("form");
            form.action = "/addToTeam";
            form.method = "post";
            hidden_num = document.createElement("input");
            hidden_num.type = "hidden";
            hidden_num.name = "addPDGANum";
            hidden_num.value = result[i].pdga_number;
            form.appendChild(hidden_num);

            hidden_league_name = document.createElement("input");
            hidden_league_name.type = "hidden";
            hidden_league_name.value = document.getElementById("leagueNameDropdown").innerText;
            hidden_league_name.name = "leagueName";
            form.appendChild(hidden_league_name);

            hidden_division_name = document.createElement("input");
            hidden_division_name.type = "hidden";
            hidden_division_name.value = result[i].division;
            hidden_division_name.name = "playerDivision";
            form.appendChild(hidden_division_name);

            button = document.createElement("button");
            button.setAttribute("class", "btn btn-outline-success btn-sm");
            button.id = "add";
            button.type = "submit";
            button.innerText = "+";
            button.style.borderRadius = "100%"
            form.appendChild(button);

            form_area.appendChild(form);
        }
        rect.appendChild(form_area);

        player_name.innerText = result[i].player_name;
        player_name.setAttribute("class", "mb-1");
        player_name.className = "player-name";
        rect.appendChild(player_name);

        pdga_num = document.createElement("p");
        pdga_num.setAttribute("class", "mb-1");
        pdga_num.className = "pdga-num";
        pdga_num.innerText = "#" + result[i].pdga_number;
        rect.appendChild(pdga_num);

        rating = document.createElement("h5");
        rating.className = "rating";
        rating.innerText = result[i].rating;
        rect.appendChild(rating);

        playerArea.appendChild(rect);
    }
}

function clearInput() {
    console.log("Clearing input");
    document.getElementById("mess").value = "";
}

window.addEventListener("load", setup);