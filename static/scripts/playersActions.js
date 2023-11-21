function setup() {
    document.getElementById("searchButton").addEventListener("click", search);
    document.getElementById('sortByRating').addEventListener("click", () => {sort("rating");});
    document.getElementById('sortByPdgaNum').addEventListener("click", () => {sort("pdga-num")});
    document.getElementById('sortByName').addEventListener("click", () => {sort("name")});
    document.getElementById('sortByPoints').addEventListener("click", () => {sort("points")});
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
        player_name = document.createElement("h5");
        rect.href = "#";
        rect.setAttribute("class", "list-group-item list-group-item-action");
        rect.id = result[i].pdga_number;

        if(document.getElementById("navbarSupportedContent").contains(document.getElementById("leagueDropdown")) && ((result[i].division == "MPO" && result[0].mpoPlayers < 5) || (result[i].division == "FPO" && result[0].fpoPlayers < 3))) {
            form_area = document.createElement("div");
            form_area.className = "add-button-area";

            form = document.createElement("form");
            form.action = "/addToTeam";
            form.method = "post";
            hidden_num = document.createElement("input");
            hidden_num.type = "hidden";
            hidden_num.name = "addPDGANum";
            hidden_num.value = result[i].pdga_number;
            form.appendChild(hidden_num);

            hidden_draft = document.createElement("input");
            hidden_draft.type = "hidden";
            hidden_draft.name = "draft";
            hidden_draft.value = "no";
            form.appendChild(hidden_draft);

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
            rect.appendChild(form_area);
        }

        player_name.innerText = result[i].player_name;
        player_name.setAttribute("class", "mb-1");
        player_name.className = "player-name";
        rect.appendChild(player_name);

        pdga_num = document.createElement("p");
        pdga_num.setAttribute("class", "mb-1");
        pdga_num.className = "pdga-num";
        pdga_num.innerText = "#" + result[i].pdga_number;
        rect.appendChild(pdga_num);

        top10Area = document.createElement("div");
        top10Area.className = "statArea";

        top10 = document.createElement("h5");
        top10.className = "stat";
        top10.innerText = result[i].top_10;
        top10Area.appendChild(top10);
        rect.appendChild(top10Area);

        winArea = document.createElement("div");
        winArea.className = "statArea";

        win = document.createElement("h5");
        win.className = "stat";
        win.innerText = result[i].wins;
        winArea.appendChild(win);
        rect.appendChild(winArea);

        eventsArea = document.createElement("div");
        eventsArea.className = "statArea";

        events = document.createElement("h5");
        events.className = "stat";
        events.innerText = result[i].events;
        eventsArea.appendChild(events);
        rect.appendChild(eventsArea);

        pointsArea = document.createElement("div");
        pointsArea.className = "statArea";

        points = document.createElement("h5");
        points.className = "stat";
        points.innerText = result[i].points;
        pointsArea.appendChild(points);
        rect.appendChild(pointsArea);

        ratingArea = document.createElement("div");
        ratingArea.className = "statArea";

        rating = document.createElement("h5");
        rating.className = "stat";
        rating.innerText = result[i].rating;
        ratingArea.appendChild(rating);
        rect.appendChild(ratingArea);


        playerArea.appendChild(rect);
    }
}


/*
Code for popup window when player is clicked on

closePopup.addEventListener("click", function () {
    myPopup.classList.remove("show");
});
window.addEventListener("click", function (event) {
    if (event.target == myPopup) {
        myPopup.classList.remove("show");
    }
});

let elementsArray = document.querySelectorAll("a.list-group-item");

elementsArray.forEach(function(elem) {
    elem.addEventListener("click", function() {
        let text = document.getElementById("textPdga");
        text.innerText = elem.id;
        myPopup.classList.add("show");
    });
});*/

function clearInput() {
    console.log("Clearing input");
    document.getElementById("mess").value = "";
}

window.addEventListener("load", setup);