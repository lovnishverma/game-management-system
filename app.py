from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc#203$@sir'  # Replace with a strong random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Database filename

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Donationsnew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(100), nullable=False)
    donor_type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    donation_date = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Kolkata')))

class UserDonation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_donated = db.Column(db.Float, default=0.0, nullable=False)


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    membertype = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    mobile_number = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    user_class = db.Column(db.String(50))
    year = db.Column(db.String(200))
    

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
        mobile_number = request.form['mobile_number']
        gender = request.form['gender']
        user_class = request.form['user_class']
        year = request.form['year']

        user = User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists. Please choose a different username.', 'error')
        else:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already exists. Please choose a different email.', 'error')
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(
                    fname=fname,
                    username=username,
                    membertype=membertype,
                    email=email,
                    password=hashed_password,
                    mobile_number=mobile_number,
                    gender=gender,
                    user_class=user_class,
                    year=year
                )
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

@app.route('/leave_team/<int:team_id>', methods=['POST'])
@login_required
def leave_team(team_id):
    team = Team.query.get(team_id)
    if team:
        if current_user in team.members:
            team.members.remove(current_user)
            db.session.commit()
            flash('You have left the team.', 'success')
        else:
            flash('You are not a member of this team.', 'error')
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


@app.route('/admin/manage_teams')
@login_required
def manage_teams():
    if current_user.is_authenticated and current_user.username == "admin":
        # Fetch all teams from the database
        teams = Team.query.all()
        return render_template('manage_team.html', teams=teams)

    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))

@app.route('/admin/edit_team/<int:team_id>', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    # Fetch the team by its ID from the database
    team = Team.query.get(team_id)
    if not team:
        flash("Team not found.", 'error')
        return redirect(url_for('manage_teams'))

    if current_user.is_authenticated and current_user.username == "admin":
        if request.method == 'POST':
            # Retrieve the form data
            team_name = request.form['teamName']
            game_name = request.form['gameName']
            
            # Update the team details
            team.name = team_name
            team.game.game_name = game_name
            
            # Commit changes to the database
            db.session.commit()
            
            flash("Team details updated successfully.", 'success')
            return redirect(url_for('manage_teams'))

        return render_template('edit_team.html', team=team)

    flash("You do not have permission to access the Admin panel.", 'error')

    return redirect(url_for('dashboard'))

@app.route('/admin/remove_member/<int:team_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_member(team_id, user_id):
    if current_user.is_authenticated and current_user.username == "admin":
        team = Team.query.get(team_id)
        user = User.query.get(user_id)

        if team and user:
            if user in team.members:
                team.members.remove(user)
                db.session.commit()
                flash("Member removed from the team.", 'success')
            else:
                flash("Member is not part of this team.", 'error')
        else:
            flash("Team or member not found.", 'error')

        return redirect(url_for('manage_teams'))

    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))

@app.route('/admin/delete_team/<int:team_id>', methods=['POST'])
@login_required
def delete_team(team_id):
    if current_user.is_authenticated and current_user.username == "admin":
        team = Team.query.get(team_id)
        if team:
            db.session.delete(team)
            db.session.commit()
            flash("Team '{}' has been deleted.".format(team.name), 'success')
        else:
            flash("Team not found.", 'error')
    else:
        flash("You do not have permission to perform this action.", 'error')

    return redirect(url_for('manage_teams'))


  
# Flask Route to View and Edit Profile
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update profile information in the database based on the form data
        current_user.fname = request.form['fname']
        current_user.username = request.form['username']
        current_user.gender = request.form['gender']
        current_user.user_class = request.form['user_class']
        current_user.year = request.form['year']

        db.session.commit()
        flash("Profile information updated successfully.", 'success')

    return render_template('profile.html', user=current_user)

# Flask Route to Change Password
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']

    if check_password_hash(current_user.password, current_password):
        hashed_new_password = generate_password_hash(new_password)
        current_user.password = hashed_new_password
        db.session.commit()
        flash("Password changed successfully.", 'success')
    else:
        flash("Incorrect current password.", 'error')

    return redirect(url_for('profile'))

# Flask Route to Update Contact Details
@app.route('/update_contact', methods=['POST'])
@login_required
def update_contact():
    new_email = request.form['new_email']
    new_mobile_number = request.form['new_mobile_number']

    # Update contact details in the database
    current_user.email = new_email
    current_user.mobile_number = new_mobile_number
    db.session.commit()

    flash("Contact details updated successfully.", 'success')
    return redirect(url_for('profile'))

# Admin Panel - User Teams
@app.route('/admin/user_teams')
@login_required
def user_teams():
    if current_user.is_authenticated and current_user.username == "admin":
        users = User.query.all()

        user_teams_info = []
        for user in users:
            user_info = {
                'user': user,
                'joined_teams': [],
            }
            for team in user.teams:
                user_info['joined_teams'].append({
                    'game_name': team.game.game_name,
                    'team_name': team.name,
                })
            user_teams_info.append(user_info)

        return render_template('user_teams.html', user_teams_info=user_teams_info)

    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        donor_name = request.form['donor_name']
        donor_type = request.form['donor_type']
        donation_amount = float(request.form['donation_amount'])

        if donor_name and donor_type and donation_amount > 0:
            new_donation = Donationsnew(donor_name=donor_name, donor_type=donor_type, amount=donation_amount)
            db.session.add(new_donation)
            db.session.commit()
            flash('Thank you for your donation!', 'success')
        else:
            flash('Please provide valid donor name, donor type, and donation amount.', 'error')

    return redirect(url_for('view_donations'))

@app.route('/view_donations')
def view_donations():
    all_donations = Donationsnew.query.order_by(Donationsnew.amount.desc()).all()
    total_collected = sum(donation.amount for donation in all_donations)
    
    return render_template("view_donations.html", donations=all_donations, total_collected=total_collected)

@app.route('/admin/change_user_team/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_change_user_team(user_id):
    if current_user.is_authenticated and current_user.username == "admin":
        user = User.query.get(user_id)
        
        if not user:
            flash("User not found.", 'error')
            return redirect(url_for('manage_teams'))  # Redirect to admin's team management page
        
        if request.method == 'POST':
            new_team_id = int(request.form['new_team_id'])
            new_team = Team.query.get(new_team_id)
            
            if not new_team:
                flash("Team not found.", 'error')
                return redirect(url_for('admin_change_user_team', user_id=user_id))
            
            user.team = new_team
            db.session.commit()
            
            flash("{}'s team has been updated.".format(user.username), 'success')
            return redirect(url_for('manage_teams'))  # Redirect to admin's team management page
        
        teams = Team.query.all()
        return render_template('admin_change_user_team.html', user=user, teams=teams)
    
    flash("You do not have permission to access the Admin panel.", 'error')
    return redirect(url_for('dashboard'))


@app.route('/donation')
def donation():
    return render_template("donate.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()