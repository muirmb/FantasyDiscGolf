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
    curr_num_users = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    def __init__(self, league_name, max_num_users, password, owner_id):
        self.league_name = league_name
        self.password = password
        self.max_num_users = max_num_users
        self.owner_id = owner_id
        self.curr_num_users = 0

# User owns player in League
class Owns(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    pdga_number = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, primary_key=True)
    def __init__(self, user, player, league):
        self.user_id = user
        self.pdga_number = player
        self.league_id = league

# Holds players' tournament data
class TourPlayer(db.Model):
    player_name = db.Column(db.String(32), nullable=False)
    pdga_number = db.Column(db.Integer, primary_key=True)
    tour_number = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    division = db.Column(db.String(8), nullable=False)
    def __init__(self, name, pdga_number, tour_num, points, rating, division):
        self.player_name = name
        self.pdga_number = pdga_number
        self.tour_number = tour_num
        self.points = points
        self.rating = rating
        self.division = division

class UserInLeague(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False)
    league_id = db.Column(db.Integer, primary_key=True)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    ties = db.Column(db.Integer, nullable=False)
    totalPoints = db.Column(db.Integer, nullable=False)
    def __init__(self, user_id, league_id, username):
        self.user_id = user_id
        self.username = username
        self.league_id = league_id
        self.wins = 0
        self.losses = 0
        self.ties = 0
        self.totalPoints = 0

class Tournament(db.Model):
    tour_num = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    location = db.Column(db.String(32), nullable=False)
    dates = db.Column(db.String(24))
    def __init__(self, num, name, loc, dates):
        self.tour_num = num
        self.name = name
        self.location = loc
        self.dates = dates



#--- ROUTES ---#


@app.route("/")
def home():
    #getTourInfoAndPlayers()
    #addOwns()
    login = "Login"
    leagues = []
    admin = False
    if 'user' in session:
        login = "Logout"
        inLeagues = UserInLeague.query.filter_by(user_id=session['id'])
        for l in inLeagues:
            leagues.append(League.query.filter_by(league_id=l.league_id).first())
        if session['user'] == "Matt":
            admin = True
    tournaments = Tournament.query.all()
    return render_template("home.html", leagues=leagues, login=login, tournaments=tournaments, admin=admin)

@app.route("/league", methods=['GET','POST'])
def league():
    if 'user' in session:
        # Get all leagues to display
        leagues = League.query.all()
        if request.method == "POST":
            if request.form['form'] == "join":
                result = add_user_to_league(request.form['league_join_name'])
                if result == 1:
                    error="You are already in that league."
                    return render_template("league.html", inLeague=False, login="Logout", leagues=leagues, error_join=error)
                return redirect(url_for('inside_league', name=request.form['league_join_name']))
            else:
                leagueName = request.form['league_name']
                if League.query.filter_by(league_name=leagueName).first() != None:
                    return render_template("league.html", inLeague=False, login="Logout", leagues=leagues, error_create="That league name is taken")
                db.session.add(League(leagueName, request.form['max_users'], request.form['league_password'], session['id']))
                db.session.commit()
                add_user_to_league(request.form['league_name'])
                return redirect(url_for('inside_league', name=request.form['league_name']))
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
            return redirect(url_for('account'))
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
            return redirect(url_for('login'))
    return render_template("register.html", error=error)

@app.route("/account")
def account():
    login = "Login"
    if 'user' in session:
        login = "Logout"
        currUser = User.query.filter_by(user_id=session['id']).first()
        return render_template("account.html", login=login, user=currUser, leagues=['I', 'D', 'I', 'O', 'T'])
    return redirect(url_for('login'))

@app.route("/changePassword")
def changePassword():
    return render_template("changePassword.html")

@app.route("/players")
def players():
    p = TourPlayer.query.filter_by(tour_number=65288)
    login = "Login"
    if 'user' in session:
        login = "Logout"
    return render_template("players.html", players=p, login=login)

@app.route("/sortPlayers", methods=['GET', 'POST'])
def sortPlayers():
    sortJson = request.get_json()
    playersObjects = TourPlayer.query.filter_by(tour_number=65288)
    players = []
    for player in playersObjects:
        players.append({'player_name':player.player_name, 'pdga_number':player.pdga_number, 'tour_number':player.tour_number, 'points':player.points, 'rating':player.rating, 'division':player.division})

    if sortJson['league'] != "":
        ownedInLeague = Owns.query.filter_by(league_id=getLeagueIDByName(sortJson['league']))
        for owned in ownedInLeague:
            for player in players:
                if player['pdga_number'] == owned.pdga_number:
                    players.remove(player)
    if sortJson['attr'] == "rating":
        players.sort(reverse=True, key=sortByRating)
    elif sortJson['attr'] == "pdga-num":
        players.sort(key=sortByPdgaNum)
    elif sortJson['attr'] == "name":
        players.sort(key=sortByName)
    return json.dumps(players)

@app.route("/search", methods=['GET','POST'])
def search():
    searchJson = request.get_json()
    if searchJson['selection'] == "all":
        players = TourPlayer.query.filter_by(tour_number=65288)
    else:
        avPlayers = TourPlayer.query.filter_by(tour_number=65288)
        players = []
        for p in avPlayers:
            players.append(p)
        ownedInLeague = Owns.query.filter_by(league_id=getLeagueIDByName(searchJson['league']))
        for owned in ownedInLeague:
            for player in players:
                if player.pdga_number == owned.pdga_number:
                    players.remove(player)
    matches = []
    searchString = searchJson['string']
    for player in players:
        if player.player_name.rfind(searchString) > -1:
            matches.append({'player_name':player.player_name, 'pdga_number':player.pdga_number, 'tour_number':player.tour_number, 'points':player.points, 'rating':player.rating, 'division':player.division})
    return json.dumps(matches)

@app.route("/addToTeam", methods=['GET', 'POST'])
def addToTeam():
    league = request.form["leagueName"]
    db.session.add(Owns(session['id'], request.form["addPDGANum"], getLeagueIDByName(league)))
    db.session.commit()
    return redirect(url_for('myTeam', name=league))

@app.route("/admin")
def admin():
    return render_template("admin.html")



#--- SPECIFIC LEAGUE ---#


@app.route("/<name>/league", methods=['GET', 'POST'])
def inside_league(name):
    login = "Login"
    if 'user' in session:
        login = "Logout"
        usersInLeague = UserInLeague.query.filter_by(league_id=getLeagueIDByName(name))
        return render_template("inside_league.html", login=login, leagueName=name, users=usersInLeague)
    else:
        return redirect(url_for('login'))

@app.route("/<name>/availablePlayers")
def availablePlayers(name):
    login = "Login"
    if 'user' in session:
        login = "Logout"
        avPlayers = TourPlayer.query.filter_by(tour_number=65288)
        avPlayersList = []
        for p in avPlayers:
            avPlayersList.append(p)
        ownedInLeague = Owns.query.filter_by(league_id=getLeagueIDByName(name))
        for owned in ownedInLeague:
            for player in avPlayersList:
                if player.pdga_number == owned.pdga_number:
                    avPlayersList.remove(player)
        return render_template("players.html", players=avPlayersList, login=login, leagueName=name, tournament=Tournament.query.filter_by(tour_num=65288).first())
    else:
        return redirect(url_for('login'))

@app.route("/<name>/myTeam")
def myTeam(name):
    totalPoints = 0
    login = "Login"
    if 'user' in session:
        login = "Logout"
        owned = []
        userOwns = Owns.query.filter_by(user_id=session['id'], league_id=getLeagueIDByName(name))
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

        return render_template("myTeam.html", username=session['user'], login=login, mpoPlayers=mpoPlayers, fpoPlayers=fpoPlayers, total=totalPoints, leagueName=name)
    else:
        return redirect(url_for("login"))

@app.route("/<name>/matchup")
def matchup(name):
    return render_template("matchup.html", leagueName=name)


#--- METHODS ---#


def add_user_to_league(league_name):
    league = League.query.filter_by(league_name=league_name).first()
    if UserInLeague.query.filter_by(league_id=league.league_id, user_id=session['id']).first() != None:
        return 1
    db.session.add(UserInLeague(session['id'], league.league_id, session['user']))
    league.curr_num_users += 1
    db.session.commit()
    return 0

def getLeagueIDByName(name):
    return League.query.filter_by(league_name=name).first().league_id


#--- SORTING KEY METHODS ---#
    
def sortByRating(player):
    return player['rating']

def sortByPdgaNum(player):
    return player['pdga_number']

def sortByName(player):
    return player['player_name']


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

def getTourInfoAndPlayers():
    tour_num = 65288
    r = requests.get("https://www.pdga.com/tour/event/"+str(tour_num))
    soup = BeautifulSoup(r.text, 'html.parser')
    name = soup.find('div', attrs={'class': "panel-pane pane-page-title"}).h1.text
    info_list = soup.find('ul', attrs={'class':'event-info info-list'})
    dates = info_list.find('li', attrs={'class':'tournament-date'}).text[6:]
    location = info_list.find('li', attrs={'class': 'tournament-location'}).text[10:]
    db.session.add(Tournament(tour_num, name, location, dates))
    db.session.commit()

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
        db.session.add(TourPlayer(name, pdgaNum, tour_num, place, rating, "MPO"))
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
        db.session.add(TourPlayer(name, pdgaNum, tour_num, place, rating, "MPO"))
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
        db.session.add(TourPlayer(name, pdgaNum, tour_num, place, rating, "FPO"))
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
        db.session.add(TourPlayer(name, pdgaNum, tour_num, place, rating, "FPO"))
        db.session.commit()

    return 0


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)