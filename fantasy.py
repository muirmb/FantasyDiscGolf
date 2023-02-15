import json
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy.db'
db = SQLAlchemy(app)

app.secret_key = 'development key'

# User-League relationship
user_in_league = db.Table('user_in_league',
    db.Column('user_id', db.Integer, db.ForeignKey('user.user_id'), primary_key=True),
    db.Column('league_id', db.Integer, db.ForeignKey('league.league_id'), primary_key=True)
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
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    users = db.relationship('User', secondary=user_in_league, lazy='subquery', backref=db.backref('leagues', lazy=True))
    def __init__(self, league_name, max_num_users, owner_id):
        self.league_name = league_name
        self.max_num_users = max_num_users
        self.owner_id = owner_id

@app.route("/")
def home():
    login = "Login"
    if 'user' in session:
        login = "Logout"
    avPlayers = [["Ricky Wysocki", 1047, "../static/ricky.jpg", 38008], ["Eagle McMahon", 1043, "../static/eagle.jpeg", 37817]]
    return render_template("home.html", players=avPlayers, login=login)

@app.route("/myTeam")
def myTeam():
    login = "Login"
    if 'user' in session:
        login = "Logout"
        return render_template("myTeam.html", username=session['user'], login=login)
    else:
        return redirect(url_for("login"))

@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    if request.method == "POST":
        email = request.form['inputEmail']
        user = User.query.filter_by(email=email).first()
        if user is None:
            error = 'Invalid email or password'
        elif request.form['inputPassword'] != user.password:
            error = 'Invalid email or password'
        else:
            flash('You were logged in')
            session['user'] = user.username
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
    return render_template("account.html", login=login)

@app.route("/players")
def players():
    players = [["Chris Dickerson", 1044, "../static/chrisdickerson", 62467], ["Paul Mcbeth", 1050, "../static/paulmcb.png", 27523], ["Ricky Wysocki", 1047, "../static/ricky.jpg", 38008], ["Eagle McMahon", 1043, "../static/eagle.jpeg", 37817], ["Simon Lizotte", 1037, "../static/simon.jpg", 8332]]
    login = "Login"
    if 'user' in session:
        login = "Logout"
    return render_template("players.html", players=players, login=login)

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
    players = [["Chris Dickerson", 1044, "../static/chrisdickerson", 62467], ["Paul Mcbeth", 1050, "../static/paulmcb.png", 27523], ["Ricky Wysocki", 1047, "../static/ricky.jpg", 38008], ["Eagle McMahon", 1043, "../static/eagle.jpeg", 37817], ["Simon Lizotte", 1037, "../static/simon.jpg", 8332]]
    players.sort(reverse=True, key=sortByRating)
    return render_template("players.html", players=players, login=login)

@app.route("/search", methods=['GET','POST'])
def search():
    players = [["Chris Dickerson", 1044, "../static/chrisdickerson", 62467], ["Paul Mcbeth", 1050, "../static/paulmcb.png", 27523], ["Ricky Wysocki", 1047, "../static/ricky.jpg", 38008], ["Eagle McMahon", 1043, "../static/eagle.jpeg", 37817], ["Simon Lizotte", 1037, "../static/simon.jpg", 8332]]
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