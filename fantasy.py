import datetime
import json
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import modules.calc_points as calc_points
import requests
import lxml
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

app = Flask(__name__)
cred = credentials.Certificate("DatabaseKey.json")
firebase_admin.initialize_app(cred)
db2 = firestore.client()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy.db'

db = SQLAlchemy(app)

app.secret_key = 'development key'

# User class
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), unique=True, nullable=False)
    email = db.Column(db.String(32), unique=True, nullable = False)
    password = db.Column(db.String(24), nullable=False)
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

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

class Message(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(24), nullable=False)
    content = db.Column(db.String(160), nullable=False)
    def __init__(self, content, name):
        self.content = content
        self.sender_name = name

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
    place = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    division = db.Column(db.String(8), nullable=False)
    def __init__(self, name, pdga_number, tour_num, place, points, rating, division):
        self.player_name = name
        self.pdga_number = pdga_number
        self.tour_number = tour_num
        self.place = place
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
    numMPOPlayers = db.Column(db.Integer, nullable=False)
    numFPOPlayers = db.Column(db.Integer, nullable=False)
    def __init__(self, user_id, league_id, username):
        self.user_id = user_id
        self.username = username
        self.league_id = league_id
        self.wins = 0
        self.losses = 0
        self.ties = 0
        self.totalPoints = 0
        self.numMPOPlayers = 0
        self.numFPOPlayers = 0

class Tournament(db.Model):
    tour_num = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    location = db.Column(db.String(32), nullable=False)
    dates = db.Column(db.String(24))
    def __init__(self, num, name, loc, dates):
        self.tour_num = num
        self.name = name
        self.location = loc
        self.dates = dates

class PlayerStats(db.Model):
    player_name = db.Column(db.String(32), nullable=False)
    pdga_number = db.Column(db.Integer, primary_key=True)
    total_points = db.Column(db.Integer, nullable=False)
    events_played = db.Column(db.Integer, nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    top_10_finishes = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    division = db.Column(db.String(8), nullable=False)
    def __init__(self, name, num, points, events, win, top, rating, div):
        self.player_name = name
        self.pdga_number = num
        self.total_points = points
        self.events_played = events
        self.wins = win
        self.top_10_finishes = top
        self.rating = rating
        self.division = div


#--- ROUTES ---#


@app.route("/")
def home():
    #getTourInfoAndPlayers()
    #addOwns()
    #makeMatchups(10,10)
    tournaments = []
    docs = db2.collection(u'Tournaments').stream()
    
    for doc in docs:
        tournaments.append(doc.to_dict())
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

        # Get names of leagues the user is in
        uInL = UserInLeague.query.filter_by(user_id=session['id'])
        leagues = []
        for l in uInL:
            leagues.append(League.query.filter_by(league_id=l.league_id).first())

        return render_template("account.html", login=login, user=currUser, leagues=leagues)
    return redirect(url_for('login'))

@app.route("/changePassword")
def changePassword():
    return render_template("changePassword.html")

@app.route("/players")
def players():
    p = PlayerStats.query.all()
    login = "Login"
    if 'user' in session:
        login = "Logout"
    return render_template("players.html", players=p, login=login)

@app.route("/sortPlayers", methods=['GET', 'POST'])
def sortPlayers():
    sortJson = request.get_json()
    playersObjects = PlayerStats.query.all()

    players = []
    for player in playersObjects:
        players.append({'player_name':player.player_name, 'pdga_number':player.pdga_number, 'points':player.total_points, 'events':player.events_played, 'wins': player.wins, 'top_10':player.top_10_finishes, 'rating':player.rating, 'division':player.division})

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
    elif sortJson['attr'] == 'points':
        players.sort(reverse=True, key=sortByPoints)

    # Add how many spots are filled in the users roster, if necessary
    if sortJson['league'] != "":
        user = UserInLeague.query.filter_by(user_id=session['id'], league_id=getLeagueIDByName(sortJson['league'])).first()
        players.insert(0, {'mpoPlayers': user.numMPOPlayers, 'fpoPlayers': user.numFPOPlayers})

    return json.dumps(players)

@app.route("/search", methods=['GET','POST'])
def search():
    searchJson = request.get_json()
    matches = []
    if searchJson['selection'] == "all":
        players = TourPlayer.query.all()
    else:
        avPlayers = TourPlayer.query.all()
        players = []
        for p in avPlayers:
            players.append(p)
        ownedInLeague = Owns.query.filter_by(league_id=getLeagueIDByName(searchJson['league']))
        for owned in ownedInLeague:
            for player in players:
                if player.pdga_number == owned.pdga_number:
                    players.remove(player)
    searchString = searchJson['string']
    for player in players:
        if player.player_name.rfind(searchString) > -1:
            matches.append({'player_name':player.player_name, 'pdga_number':player.pdga_number, 'tour_number':player.tour_number, 'points':player.points, 'rating':player.rating, 'division':player.division})
    if searchJson['league'] != "":
        user = UserInLeague.query.filter_by(user_id=session['id'], league_id=getLeagueIDByName(searchJson['league'])).first()
        matches.insert(0, {'mpoPlayers': user.numMPOPlayers, 'fpoPlayers': user.numFPOPlayers})

    return json.dumps(matches)

@app.route("/addToTeam", methods=['GET', 'POST'])
def addToTeam():
    user = UserInLeague.query.filter_by(user_id=session['id']).first()
    league = request.form["leagueName"]
    db.session.add(Owns(session['id'], request.form["addPDGANum"], getLeagueIDByName(league)))
    if request.form['playerDivision'] == 'MPO':
        user.numMPOPlayers += 1
    elif request.form['playerDivision'] == 'FPO':
        user.numFPOPlayers += 1
    db.session.commit()
    if request.form['draft'] == 'draft':
        flash('Draft selection succesful')
        return redirect(url_for('draft', name=league))
    return redirect(url_for('myTeam', name=league))

@app.route("/removeFromTeam", methods=['GET','POST'])
def removeFromTeam():
    user = UserInLeague.query.filter_by(user_id=session['id']).first()
    league = request.form["leagueName"]
    obj = Owns.query.filter_by(user_id=session['id'], pdga_number=request.form["remPDGANum"], league_id=getLeagueIDByName(league)).first()
    db.session.delete(obj)
    if request.form['playerDivision'] == 'MPO':
        user.numMPOPlayers -= 1
    elif request.form['playerDivision'] == 'FPO':
        user.numFPOPlayers -= 1
    db.session.commit()
    return redirect(url_for('myTeam', name=league))

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/getEventInfo", methods=['GET','POST'])
def getEventInfo():
    getTourInfoAndPlayers(request.form["event_num"])
    return redirect(url_for('home'))


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
        user = UserInLeague.query.filter_by(user_id=session['id'], league_id=getLeagueIDByName(name)).first()
        avPlayers = PlayerStats.query.all()
        avPlayersList = [p for p in avPlayers]
        ownedInLeague = Owns.query.filter_by(league_id=getLeagueIDByName(name))
        for owned in ownedInLeague:
            for player in avPlayersList:
                if player.pdga_number == owned.pdga_number:
                    avPlayersList.remove(player)
        return render_template("players.html", players=avPlayersList, login=login, leagueName=name, tournament=Tournament.query.filter_by(tour_num=71468).first(), user=user)
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
            player = TourPlayer.query.filter_by(pdga_number=num).first()
            if player == None:
                continue
            totalPoints += player.points
            if player.division == "MPO":
                mpoPlayers.append(player)
            elif player.division == "FPO":
                fpoPlayers.append(player)

        return render_template("myTeam.html", username=session['user'], login=login, mpoPlayers=mpoPlayers, fpoPlayers=fpoPlayers, total=totalPoints, leagueName=name)
    else:
        return redirect(url_for("login"))

@app.route("/<name>/matchup")
def matchup(name):
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
            player = TourPlayer.query.filter_by(pdga_number=num).first()
            if player == None:
                continue
            totalPoints += player.points
            if player.division == "MPO":
                mpoPlayers.append(player)
            elif player.division == "FPO":
                fpoPlayers.append(player)
        return render_template("matchup.html", leagueName=name, username=session['user'], mpoPlayers=mpoPlayers, fpoPlayers=fpoPlayers, total=totalPoints, login=login)
    else:
        return redirect(url_for("login"))

@app.route("/<name>/draft")
def draft(name):
    login = "Login"
    user = UserInLeague.query.filter_by(user_id=session['id'], league_id=getLeagueIDByName(name)).first()
    avPlayers = TourPlayer.query.all()
    avPlayersList = [p for p in avPlayers]
    ownedInLeague = Owns.query.filter_by(league_id=getLeagueIDByName(name))
    for owned in ownedInLeague:
        for player in avPlayersList:
            if player.pdga_number == owned.pdga_number:
                avPlayersList.remove(player)

    allUsers = UserInLeague.query.filter_by(league_id=getLeagueIDByName(name))
    allUsersList = [u for u in allUsers]
    draftOrder = []
    count = 0
    for i in range(6):
        for u in allUsersList:
            draftOrder.append({'username': u.username, 'id': count})
            count += 1
        allUsersList.reverse()

    return render_template("draft.html", leagueName=name, login=login, players=avPlayersList, user=user, users=draftOrder)

@app.route('/messages', methods=['GET'])
def get_items():
	allMess = Message.query.all()
	messages = []
	for mess in allMess:
		messages.append({'message_id':mess.message_id, 'content':mess.content, 'sender':mess.sender_name})
	return json.dumps(messages)

@app.route('/new_message', methods=['GET','POST'])
def add():
	newmessageJson = request.get_json()
	newmessage = Message(newmessageJson['mess'], session['user'])
	db.session.add(newmessage)
	db.session.commit()
	allMess = Message.query.all()
	messages = []
	for mess in allMess:
		messages.append({'message_id':mess.message_id, 'content':mess.content, 'sender':mess.sender_name})
	return json.dumps(messages)

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

    return name

def getTourInfoAndPlayers(tour_num):
    r = requests.get("https://www.pdga.com/tour/event/"+str(tour_num))
    soup = BeautifulSoup(r.text, 'html.parser')
    name = soup.find('div', attrs={'class': "panel-pane pane-page-title"}).h1.text
    info_list = soup.find('ul', attrs={'class':'event-info info-list'})
    dates = info_list.find('li', attrs={'class':'tournament-date'}).text[6:]
    location = info_list.find('li', attrs={'class': 'tournament-location'}).text[10:]
    if Tournament.query.filter_by(tour_num=tour_num).first() is None:
        db.session.add(Tournament(tour_num, name, location, dates))
        data = {
            'location': location,
            'name': name,
            'end': datetime.datetime.now(tz=datetime.timezone.utc),
            'start': datetime.datetime.now(tz=datetime.timezone.utc)
        }

        # Add a new doc in collection 'cities' with ID 'LA'
        db2.collection(u'Tournaments').document(name).set(data)
        db.session.commit()

    elite_top20 = [100, 85, 75, 69, 64, 60, 57, 54, 52, 50, 48, 46, 44, 42, 40, 38, 36, 34, 32, 30]
    table = soup.find_all('div', attrs={'class': 'table-container'})
    odds = table[1].find_all('tr', attrs={'class':'odd'})

    for odd in odds:
        points = 0
        if odd.find('td', attrs={'class': 'place'}) is not None:
            place = int(odd.find('td', attrs={'class': 'place'}).text)
            if place > 0 and place < 21:
                points = elite_top20[place-1]
            elif place > 20 and place < 49:
                points = 50-place
            elif place == 49 or place == 50:
                points = 2
            elif place > 50:
                points = 1
        else:
            place = 0
        pdgaNum = odd.find('td', attrs={'class': 'pdga-number'}).text
        rating = odd.find('td', attrs={'class': 'player-rating propagator'}).text
        name = odd.find('td', attrs={'class': 'player'}).a.text
        if TourPlayer.query.filter_by(tour_number=tour_num, pdga_number=pdgaNum).first() is None:
            db.session.add(TourPlayer(name, pdgaNum, tour_num, place, points, rating, "MPO"))
        else:
            player = TourPlayer.query.filter_by(pdga_number=pdgaNum, tour_number=tour_num).first()
            player.points = points
        db.session.commit()

    evens = table[1].find_all('tr', attrs={'class':'even'})

    for even in evens:
        points = 0
        if even.find('td', attrs={'class': 'place'}) is not None:
            place = int(even.find('td', attrs={'class': 'place'}).text)
            if place > 0 and place < 21:
                points = elite_top20[place-1]
            elif place > 20 and place < 49:
                points = 50-place
            elif place == 49 or place == 50:
                points = 2
            elif place > 50:
                points = 1
        else:
            place = 0
        pdgaNum = even.find('td', attrs={'class': 'pdga-number'}).text
        rating = even.find('td', attrs={'class': 'player-rating propagator'}).text
        name = even.find('td', attrs={'class': 'player'}).a.text
        if TourPlayer.query.filter_by(tour_number=tour_num, pdga_number=pdgaNum).first() is None:
            db.session.add(TourPlayer(name, pdgaNum, tour_num, place, points, rating, "MPO"))
        else:
            player = TourPlayer.query.filter_by(pdga_number=pdgaNum, tour_number=tour_num).first()
            player.points = points
        db.session.commit()

    odds = table[2].find_all('tr', attrs={'class':'odd'})

    for odd in odds:
        points = 0
        if odd.find('td', attrs={'class': 'place'}) is not None:
            place = int(odd.find('td', attrs={'class': 'place'}).text)
            if place > 0 and place < 21:
                points = elite_top20[place-1]
            elif place > 20 and place < 49:
                points = 50-place
            elif place == 49 or place == 50:
                points = 2
            elif place > 50:
                points = 1
        else:
            place = 0
        pdgaNum = odd.find('td', attrs={'class': 'pdga-number'}).text
        rating = odd.find('td', attrs={'class': 'player-rating'}).text
        name = odd.find('td', attrs={'class': 'player'}).a.text
        if TourPlayer.query.filter_by(tour_number=tour_num, pdga_number=pdgaNum).first() is None:
            db.session.add(TourPlayer(name, pdgaNum, tour_num, place, points, rating, "FPO"))
        else:
            player = TourPlayer.query.filter_by(pdga_number=pdgaNum, tour_number=tour_num).first()
            player.points = points
        db.session.commit()

    evens = table[2].find_all('tr', attrs={'class':'even'})

    for even in evens:
        points = 0
        if even.find('td', attrs={'class': 'place'}) is not None:
            place = int(even.find('td', attrs={'class': 'place'}).text)
            if place > 0 and place < 21:
                points = elite_top20[place-1]
            elif place > 20 and place < 49:
                points = 50-place
            elif place == 49 or place == 50:
                points = 2
            elif place > 50:
                points = 1
        else:
            place = 0
        pdgaNum = even.find('td', attrs={'class': 'pdga-number'}).text
        rating = even.find('td', attrs={'class': 'player-rating'}).text
        name = even.find('td', attrs={'class': 'player'}).a.text
        if TourPlayer.query.filter_by(tour_number=tour_num, pdga_number=pdgaNum).first() is None:
            db.session.add(TourPlayer(name, pdgaNum, tour_num, place, points, rating, "FPO"))
        else:
            player = TourPlayer.query.filter_by(pdga_number=pdgaNum, tour_number=tour_num).first()
            player.points = points
        db.session.commit()

    updatePlayerStats(TourPlayer.query.filter_by(tour_number=tour_num))

    return 0

def makeMatchups(teams, weeks):
    # Create all matchup pairs
    allMatchups = []
    for i in range(1,teams):
        for j in range(i+1,teams+1):
            allMatchups.append([i,j])

    weeklyMatchups = []
    for i in range(teams-1):
        thisWeek = []
        replaceLater = []
        # Make checkoff list
        checkoff = []
        for x in range(1, teams+1):
            checkoff.append(x)

        j=0
        while j < teams//2:
            print("all matches left", allMatchups)
            foundMatch = False
            for match in allMatchups:
                if match[0] in checkoff and match[1] in checkoff:
                    thisWeek.append(match)
                    checkoff.remove(match[0])
                    checkoff.remove(match[1])
                    print("checkoff now has", checkoff)
                    foundMatch = True
                    break
            if foundMatch == False:
                lastMatch = thisWeek.pop()
                checkoff.append(lastMatch[0])
                checkoff.append(lastMatch[1])
                print("checkoff now has", checkoff)
                replaceLater.append(lastMatch)
                allMatchups.remove(lastMatch)
                j = j-2
            j = j+1
        print("This week: ", thisWeek)
        # remove matchups from this week
        for match in thisWeek:
            allMatchups.remove(match)

        for match in replaceLater:
            allMatchups.append(match)
            replaceLater.remove(match)
        weeklyMatchups.append(thisWeek)

    print(weeklyMatchups)


    return 0

def updatePlayerStats(thesePlayers):
    for t in thesePlayers:
        win = 0
        top = 0

        if t.place == 1:
            win = 1
        if t.place >= 1 and t.place <= 10:
            top = 1

        player = PlayerStats.query.filter_by(pdga_number=t.pdga_number).first()
        if player is None:
            db.session.add(PlayerStats(t.player_name, t.pdga_number, t.points, 1, win, top, t.rating, t.division))
        else:
            player.total_points += t.points
            player.events_played += 1
            player.wins += win
            player.top_10_finishes += top
            player.rating = t.rating
            
    db.session.commit()

    return 0


#--- SORTING KEY METHODS ---#
    
def sortByRating(player):
    return player['rating']

def sortByPdgaNum(player):
    return player['pdga_number']

def sortByName(player):
    return player['player_name']

def sortByPoints(player):
    return player['points']


def makeSomeData():
    data = {
        u'name': u'Los Angeles',
        u'state': u'CA',
        u'country': u'USA'
    }

    # Add a new doc in collection 'cities' with ID 'LA'
    db2.collection(u'cities').document(u'LA').set(data)

if __name__ == "__main__":
    db.create_all()
    makeSomeData()
    app.run(debug=True)