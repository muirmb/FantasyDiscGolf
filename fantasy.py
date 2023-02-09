import json
from flask import Flask, redirect, url_for, render_template, request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy.db'
db = SQLAlchemy(app)

app.secret_key = 'development key'

# User-League relationship
user_in_league = db.Table('user_in_league',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Columb('league_id', db.Integer, db.ForeignKey('league.id'), primary_key=True)
)

# User class
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), unique=True, nullable=False)
    email = db.Column(db.String(32), unique=True, nullable = False)
    password = db.Column(db.String(24), nullable=False)
    total_points = db.Column(db.Integer)
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.total_points = 0

# League class
class League(db.Model):
    league_id = db.Column(db.Integer, primary_key=True)
    league_name = db.Column(db.String(24), nullable=False)
    max_num_users = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    users = db.relationship('User', secondary=user_in_league, lazy='subquery', backref=db.backref('leagues', lazy=True))
    def __init__(self, league_name, max_num_users, owner_id):
        self.league_name = league_name
        self.max_num_users = max_num_users
        self.owner_id = owner_id

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
    db.create_all()
    app.run(debug=True)