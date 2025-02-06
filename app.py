from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    preferences = db.Column(db.String(150), nullable=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        profiles = Profile.query.filter(Profile.gender.in_(user.preferences.split(','))).all()
        return render_template('home.html', profiles=profiles)
    return redirect(url_for('login'))

@app.route('/chat/<int:id>')
def chat(id):
    profile = Profile.query.get_or_404(id)
    return render_template('chat.html', profile=profile)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        age = request.form['age']
        gender = request.form['gender']
        preferences = request.form['preferences']

        new_user = User(username=username, password=password, age=age, gender=gender, preferences=preferences)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/profile/<int:id>')
def view_profile(id):
    profile = Profile.query.get_or_404(id)
    return render_template('profile.html', profile=profile)

@socketio.on('message')
def handle_message(msg):
    send(msg, broadcast=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Add sample data (only for the first run)
        if not Profile.query.first():
            sample_profiles = [
                Profile(name="Lila", age=21, gender="Female", bio="Gothic college student", image_url="static/lila.jpg"),
                Profile(name="Selene", age=19, gender="Female", bio="Alternative girl who loves gaming", image_url="static/selene.jpg"),
                Profile(name="Maddy", age=24, gender="Female", bio="HR professional from Brisbane", image_url="static/maddy.jpg")
            ]
            db.session.bulk_save_objects(sample_profiles)
            db.session.commit()

        # Atualizar registros existentes
        profiles = Profile.query.all()
        for profile in profiles:
            if profile.image_url.startswith('static/'):
                profile.image_url = profile.image_url.replace('static/', '')
        db.session.commit()

    socketio.run(app, debug=True)
