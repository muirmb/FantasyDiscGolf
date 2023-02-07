import json
from flask import Flask, redirect, url_for, render_template, request, session

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/myTeam")
def myTeam():
    return render_template("myTeam.html")

@app.route("/account")
def account():
    return render_template("account.html")

@app.route("/players")
def players():
    players = [["Chris Dickerson", 1044], ["Paul Mcbeth", 1050], ["Ricky Wysocki", 1047], ["Eagle McMahon", 1043], ["Simon Lizotte", 1037]]
    return render_template("players.html", players=players)

@app.route("/availablePlayers")
def availablePlayers():
    avPlayers = [["Ricky Wysocki", 1047], ["Eagle McMahon", 1043]]
    return render_template("players.html", players=avPlayers)

@app.route("/sortPlayers")
def sortPlayers():
    players = [["Chris Dickerson", 1044], ["Paul Mcbeth", 1050], ["Ricky Wysocki", 1047], ["Eagle McMahon", 1043], ["Simon Lizotte", 1037]]
    players.sort(reverse=True, key=sortByRating)
    return render_template("players.html", players=players)

@app.route("/search", methods=['GET','POST'])
def search():
    players = [["Paul Mcbeth", 1050], ["Ricky Wysocki", 1047], ["Eagle McMahon", 1043]]
    string = ""
    matches = []
    if request.method == 'POST':
        string = request.form['search']
    for player in players:
        if player[0].rfind(string) > -1:
            matches.append(player)
    return render_template("players.html", players=matches)

def sortByRating(player):
    return player[1]

if __name__ == "__main__":
    app.run(debug=True)