let timeoutID;
let timeout = 5000;

function setup() {
    document.getElementById("button").addEventListener("click", makePost);
    timeoutID = window.setTimeout(poller, timeout);
}

function makePost() {
    console.log("Sending POST request");
    const mess = document.getElementById("mess").value
    
    fetch("/new_message", {
            method: "post",
            headers: { "Content-type": "application/json; charset=UTF-8" },
            body: JSON.stringify({
                mess: mess
            })
        })
        .then((response) => {
            return response.json();
        })
        .then((result) => {
            updateChat(result);
            clearInput();
        })
        .catch(() => {
            console.log("Error posting new items!");
        });
}

function poller() {
    console.log("Polling for new items");
    fetch("/messages")
        .then((response) => {
            return response.json();
        })
        .then(updateChat)
        .catch(() => {
            console.log("Error fetching items!");
        });
}

function updateChat(result) {
    console.log("Updating the chat");
    chatArea = document.getElementById("chat");
    message = document.createElement("div");
    messageLabel = document.createElement("div");
    for (var i = 0; i < result.length; i++) {
        if(result[i].message_id > document.getElementById("last_id").getAttribute("value")){
            messageLabel.innerText = result[i].sender;
            messageLabel.className = "message-label";
            chatArea.appendChild(messageLabel);
            message.innerText = result[i].content;
            message.className = "message";
            chatArea.appendChild(message);
        }
    }
    chatArea.scrollTop = chatArea.scrollHeight;
    last = document.getElementById("last_id");
    last.setAttribute("value", result[result.length-1].message_id);
    console.log(last.value);
    
    timeoutID = window.setTimeout(poller, timeout);
}

function clearInput() {
    console.log("Clearing input");
    document.getElementById("mess").value = "";
}

window.addEventListener("load", setup);