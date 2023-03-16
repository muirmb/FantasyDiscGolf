import json
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import modules.calc_points as calc_points
import requests
import lxml
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy.db'
db = SQLAlchemy(app)

app.secret_key = 'development key'

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
    league_name = db.Column(db.String(24), unique=True, nullable=False)
    password = db.Column(db.String(24), nullable=False)
    max_num_users = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    def __init__(self, league_name, max_num_users, password, owner_id):
        self.league_name = league_name
        self.password = password
        self.max_num_users = max_num_users
        self.owner_id = owner_id

# User owns player in League
class Owns(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    pdga_number = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, nullable=False)
    def __init__(self, user, player):
        self.user_id = user
        self.pdga_number = player
        self.league_id = 0

# Holds players' tournament data
class TourPlayer(db.Model):
    player_name = db.Column(db.String(32), nullable=False)
    pdga_number = db.Column(db.Integer, primary_key=True)
    tour_number = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    division = db.Column(db.String(8), nullable=False)
    def __init__(self, name, pdga_number, points, rating, division):
        self.player_name = name
        self.pdga_number = pdga_number
        self.tour_number = 2
        self.points = points
        self.rating = rating
        self.division = division

class UserInLeague(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, primary_key=True)
    def __init__(self, user_id, league_id):
        self.user_id = user_id
        self.league_id = league_id


@app.route("/")
def home():
    #getTourPlayers()
    #addOwns()
    login = "Login"
    if 'user' in session:
        login = "Logout"
    avPlayers = [["Ricky Wysocki", 1047, "../static/ricky.jpg", 38008], ["Eagle McMahon", 1043, "../static/eagle.jpeg", 37817]]
    return render_template("home.html", players=avPlayers, login=login)

@app.route("/create_league", methods=['GET','POST'])
def create_league():
    db.session.add(League(request.form['league_name'], request.form['max_users'], request.form['league_password'], session['id']))
    return redirect(url_for('home'))

@app.route("/league")
def league():
    if 'user' in session:
        # Get all leagues to display
        leagues = League.query.all()
        return render_template("league.html", inLeague=False, login="Logout", leagues=leagues)
    else:
        return redirect(url_for("login"))

@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    if 'user' in session:
        session.clear()
    elif request.method == "POST":
        email = request.form['inputEmail']
        user = User.query.filter_by(email=email).first()
        if user is None:
            error = 'Invalid email or password'
        elif request.form['inputPassword'] != user.password:
            error = 'Invalid email or password'
        else:
            flash('You were logged in')
            session['user'] = user.username
            session['id'] = user.user_id
            return redirect(url_for('myTeam'))
    return render_template("login.html", error=error)

@app.route("/register", methods=['GET', 'POST'])
def register():
    error = None
    if request.method == "POST":
        username = request.form["registerUsername"]
        email = request.form["registerEmail"]
        if not User.query.filter_by(email=email).first() is None:
            error = "This email has already been used to make an account"
        elif not User.query.filter_by(username=username).first() is None:
            error = "This username is already taken"
        elif len(request.form['registerPassword']) < 8:
            error = "Password must be at least 8 characters long"
        elif request.form['registerPassword'] != request.form['reregisterPassword']:
            error = "Passwords do not match"
        else:
            db.session.add(User(username, email, request.form['registerPassword']))
            db.session.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('myTeam'))
    return render_template("register.html", error=error)

@app.route("/account")
def account():
    login = "Login"
    if 'user' in session:
        login = "Logout"
    return render_template("account.html", login=login, leagues=['I', 'D', 'I', 'O', 'T'])

@app.route("/changePassword")
def changePassword():
    return render_template("changePassword.html")

@app.route("/players")
def players():
    p = TourPlayer.query.filter_by(tour_number=2)
    mpoPlayers = []
    fpoPlayers = []

    for player in p:
        parr = []
        parr.append(player.player_name)
        parr.append(player.points)
        parr.append(player.pdga_number)
        parr.append(player.rating)
        if player.division == "MPO":
            mpoPlayers.append(parr)
        elif player.division == "FPO":
            fpoPlayers.append(parr)

    login = "Login"
    if 'user' in session:
        login = "Logout"
    return render_template("players.html", players=mpoPlayers, login=login)

@app.route("/availablePlayers")
def availablePlayers():
    login = "Login"
    if 'user' in session:
        login = "Logout"
    avPlayers = [["Ricky Wysocki", 1047, "../static/ricky.jpg", 38008], ["Eagle McMahon", 1043, "../static/eagle.jpeg", 37817]]
    return render_template("players.html", players=avPlayers, login=login)

@app.route("/sortPlayers")
def sortPlayers():
    login = "Login"
    if 'user' in session:
        login = "Logout"
    players=[]
    p = TourPlayer.query.filter_by(tour_number=2)
    for player in p:
        parr = []
        parr.append(player.player_name)
        parr.append(player.points)
        parr.append(player.pdga_number)
        parr.append(player.rating)
        players.append(parr)
    players.sort(reverse=True, key=sortByRating)
    return render_template("players.html", players=players, login=login)

@app.route("/search", methods=['GET','POST'])
def search():
    players = TourPlayer.query.filter_by(tour_number=2)
    string = ""
    matches = []
    login = "Login"
    if 'user' in session:
        login = "Logout"
    if request.method == 'POST':
        string = request.form['search']
    for player in players:
        if player.player_name.rfind(string) > -1:
            parr = []
            parr.append(player.player_name)
            parr.append(player.points)
            parr.append(player.pdga_number)
            parr.append(player.rating)
            matches.append(parr)
    return render_template("players.html", players=matches, login=login)

def addOwns():
    db.session.add(Owns(1, 37817))
    db.session.add(Owns(1, 44382))
    db.session.add(Owns(1, 17295))
    db.session.add(Owns(1, 98091))
    db.session.add(Owns(1, 44184))
    db.session.commit()

@app.route("/myTeam")
def myTeam():
    totalPoints = 0
    login = "Login"
    if 'user' in session:
        login = "Logout"
        owned = []
        userOwns = Owns.query.filter_by(user_id=session['id'])
        for obj in userOwns:
            owned.append(obj.pdga_number)
        mpoPlayers = []
        fpoPlayers = []
        
        for num in owned:
            parr = []
            player = TourPlayer.query.filter_by(pdga_number=num).first()
            if player == None:
                continue
            totalPoints += player.points
            parr.append(player.player_name)
            parr.append(player.points)
            parr.append(player.pdga_number)
            parr.append(player.rating)
            if player.division == "MPO":
                mpoPlayers.append(parr)
            elif player.division == "FPO":
                fpoPlayers.append(parr)

        return render_template("myTeam.html", username=session['user'], login=login, mpoPlayers=mpoPlayers, fpoPlayers=fpoPlayers, total=totalPoints)
    else:
        return redirect(url_for("login"))

@app.route("/addToTeam", methods=['GET', 'POST'])
def addToTeam():
    db.session.add(Owns(session['id'], request.form["addPDGANum"]))
    db.session.commit()
    return redirect(url_for('myTeam'))

def sortByRating(player):
    return player[3]

def getName(pdgaNum):
    r = requests.get("https://www.pdga.com/player/"+str(pdgaNum))
    soup = BeautifulSoup(r.text, 'html.parser')
    insideArea = soup.find('div', attrs={'class':'inside'})

    header = insideArea.find('h1').text
    name = header[0:(header.index('#')-len(header)-1)]
    pdgaNum = header[header.index('#')+1:len(header)]

    ratingArea = insideArea.find('li', attrs={'class':'current-rating'}).text
    rating = ratingArea[ratingArea.index(':')+2:ratingArea.index('(')-1]

    careerWins = insideArea.find('li', attrs={'class':'career-wins'}).a.text

    return careerWins

def getTourPlayers():
    r = requests.get("https://www.pdga.com/tour/event/66457")
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find_all('div', attrs={'class': 'table-container'})
    odds = table[1].find_all('tr', attrs={'class':'odd'})

    for odd in odds:
        if odd.find('td', attrs={'class': 'place'}) is not None:
            place = odd.find('td', attrs={'class': 'place'}).text
        else:
            place = 0
        pdgaNum = odd.find('td', attrs={'class': 'pdga-number'}).text
        rating = odd.find('td', attrs={'class': 'player-rating propagator'}).text
        name = odd.find('td', attrs={'class': 'player'}).a.text
        db.session.add(TourPlayer(name, pdgaNum, place, rating, "MPO"))
        db.session.commit()

    evens = table[1].find_all('tr', attrs={'class':'even'})

    for even in evens:
        if even.find('td', attrs={'class': 'place'}) is not None:
            place = even.find('td', attrs={'class': 'place'}).text
        else:
            place = 0
        pdgaNum = even.find('td', attrs={'class': 'pdga-number'}).text
        rating = even.find('td', attrs={'class': 'player-rating propagator'}).text
        name = even.find('td', attrs={'class': 'player'}).a.text
        db.session.add(TourPlayer(name, pdgaNum, place, rating, "MPO"))
        db.session.commit()

    odds = table[2].find_all('tr', attrs={'class':'odd'})

    for odd in odds:
        if odd.find('td', attrs={'class': 'place'}) is not None:
            place = odd.find('td', attrs={'class': 'place'}).text
        else:
            place = 0
        pdgaNum = odd.find('td', attrs={'class': 'pdga-number'}).text
        rating = odd.find('td', attrs={'class': 'player-rating'}).text
        name = odd.find('td', attrs={'class': 'player'}).a.text
        db.session.add(TourPlayer(name, pdgaNum, place, rating, "FPO"))
        db.session.commit()

    evens = table[2].find_all('tr', attrs={'class':'even'})

    for even in evens:
        if even.find('td', attrs={'class': 'place'}) is not None:
            place = even.find('td', attrs={'class': 'place'}).text
        else:
            place = 0
        pdgaNum = even.find('td', attrs={'class': 'pdga-number'}).text
        rating = even.find('td', attrs={'class': 'player-rating'}).text
        name = even.find('td', attrs={'class': 'player'}).a.text
        db.session.add(TourPlayer(name, pdgaNum, place, rating, "FPO"))
        db.session.commit()

    return 0


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)