from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc#203$@sir'  # Replace with a strong random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database1.db'  # Database filename

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    membertype = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile_photo = db.Column(db.String(200))
    gender = db.Column(db.String(20))
    user_class = db.Column(db.String(50))
    mobile_number = db.Column(db.String(20))

    def __repr__(self):
        return "<User {}>".format(self.username)

# Game model
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_image = db.Column(db.String(200), nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    game_details = db.Column(db.Text, nullable=False)
    team_size = db.Column(db.Integer, nullable=False)  

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    game = db.relationship('Game', backref='teams')
    members = db.relationship('User', secondary='user_team', backref='teams')

# Intermediate table for many-to-many relationship between User and Team
user_team = db.Table(
    'user_team',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'))
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.create_all()

@app.route('/')
@login_required
def dashboard():
    # Helper function to read and update visitor count
    def get_visitor_count():
        with open("visitor_count.txt", "r") as f:
            count = int(f.read())
        count += 1
        with open("visitor_count.txt", "w") as f:
            f.write(str(count))
        return count
    
    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Define the timezone for India (IST)
    tz = pytz.timezone('Asia/Kolkata')

    # Get the UTC offset for the India time zone
    india_offset = timedelta(seconds=tz.utcoffset(utc_now).total_seconds())

    # Add the UTC offset to the current UTC time to get India time
    india_time = utc_now + india_offset

    # Extract date and time components in 12-hour format
    date = india_time.strftime("%Y-%m-%d")
    time = india_time.strftime("%I:%M %p")

    # Extract only the year from the date
    year = india_time.strftime("%Y")

    # Get the current hour in the India time zone
    india_hour = india_time.hour

    # Determine the time of day based on the current hour
    if 5 <= india_hour < 12:
        time_of_day = 'Morning'
    elif 12 <= india_hour < 17:
        time_of_day = 'Afternoon'
    elif 17 <= india_hour < 21:
        time_of_day = 'Evening'
    else:
        time_of_day = 'Night'
    
    # Get the visitor count
    visitor_count = get_visitor_count()
    username = current_user.fname  # Get the username of the current user
    
    # Fetch all games from the database
    games = Game.query.all()

    return render_template("main.html", games=games, username=username, time_of_day=time_of_day, date=date, time=time, year=year, visitor_count=visitor_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fname = request.form['fname']
        username = request.form['username']
        membertype = request.form['membertype']
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists. Please choose a different username.', 'error')
        else:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already exists. Please choose a different email.', 'error')
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(fname=fname, username=username, membertype=membertype, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful. You can now log in.', 'success')
                return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/create_team/<int:game_id>', methods=['GET', 'POST'])
@login_required
def create_team(game_id):
    game = Game.query.get(game_id)
    if game:
        if request.method == 'POST':
            team_name = request.form['team_name']

            new_team = Team(name=team_name, game=game, members=[current_user])
            db.session.add(new_team)
            db.session.commit()

            flash('Team created successfully!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('create_team.html', game=game)

    flash('Game not found.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/join_team/<int:team_id>', methods=['POST'])
@login_required
def join_team(team_id):
    team = Team.query.get(team_id)
    if team:
        if current_user not in team.members:
            team.members.append(current_user)
            db.session.commit()
            flash('Joined team {}!'.format(team.name), 'success')
        else:
            flash('You are already a member of this team.', 'info')
    else:
        flash('Team not found.', 'error')

    return redirect(url_for('dashboard'))
  
@app.route('/users')
@login_required
def list_users():
    if current_user.username == "admin":
        users = User.query.all()
        return render_template('user_list.html', users=users)
    else:
        flash("You do not have permission to access Admin page.", 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.username == "admin":
        if current_user.id == user_id:
            flash("You cannot delete your own account.", 'error')
        else:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash("User '{}' has been deleted.".format(user.username), 'success')
            else:
                flash("User not found.", 'error')
    else:
        flash("You do not have permission to perform this action.", 'error')
    return redirect(url_for('list_users'))


# Admin Panel - Main Page
@app.route('/admin')
@login_required
def admin_panel():
    if current_user.is_authenticated and current_user.username == "admin":
        return render_template('admin_panel.html')
    
    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))

# Admin Panel - Add New Game
@app.route('/admin/add_game', methods=['GET', 'POST'])
@login_required
def add_game():
    if current_user.is_authenticated and current_user.username == "admin":
        if request.method == 'POST':
            game_image = request.form['gameImage']
            game_name = request.form['gameName']
            game_details = request.form['gameDetails']
            team_size = request.form['teamsize']

            # Store the game data in the database
            new_game = Game(
                game_image=game_image,
                game_name=game_name,
                game_details=game_details,
                team_size=team_size
            )
            db.session.add(new_game)
            db.session.commit()
            flash("Game added successfully.", 'success')
            return redirect(url_for('admin_panel'))

        return render_template('add_game.html')

    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))
# Admin Panel - List Games
@app.route('/admin/list_games')
@login_required
def list_games():
    if current_user.is_authenticated and current_user.username == "admin":
        games = Game.query.all()
        return render_template('list_games.html', games=games)

    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))

# Admin Panel - Modify Game
@app.route('/admin/modify_game/<int:game_id>', methods=['GET', 'POST'])
@login_required
def modify_game(game_id):
    if current_user.is_authenticated and current_user.username == "admin":
        game_to_modify = Game.query.get(game_id)

        if game_to_modify is None:
            flash("Game not found.", 'error')
            return redirect(url_for('admin_panel'))

        if request.method == 'POST':
            game_to_modify.game_image = request.form['gameImage']
            game_to_modify.game_name = request.form['gameName']
            game_to_modify.game_details = request.form['gameDetails']
            game_to_modify.team_size = request.form['teamsize']

            db.session.commit()
            flash("Game updated successfully.", 'success')
            return redirect(url_for('admin_panel'))

        return render_template('modify_game.html', game=game_to_modify)

    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))


# Admin Panel - Delete Game
@app.route('/admin/delete_game/<int:game_id>', methods=['POST'])
@login_required
def delete_game(game_id):
    if current_user.is_authenticated and current_user.username == "admin":
        game_to_delete = Game.query.get(game_id)

        if game_to_delete is None:
            flash("Game not found.", 'error')
        else:
            db.session.delete(game_to_delete)
            db.session.commit()
            flash("Game deleted successfully.", 'success')
    return redirect(url_for('admin_panel'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
