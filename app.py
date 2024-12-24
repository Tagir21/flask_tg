from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user, login_required
from flask_migrate import Migrate

from datetime import datetime
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
db = SQLAlchemy(app)
app.app_context().push()

app.secret_key = 'my_secret_key'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

class Horoscope(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sign = db.Column(db.String(20), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Horoscope %r>' % self.id

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(40), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Message %r>' % self.id

class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(40), nullable=False)
    command = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Command %r>' % self.id

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    salt = db.Column(db.String(20), default=bcrypt.gensalt())
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', name='fk_user_role'), nullable=False)
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    def is_role(self):
        return self.role.name

    def __repr__(self):
        return f'<User %r>'
def create_roles(array_of_roles):
    for role_name in array_of_roles:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            db.session.add(role)
            db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    horoscopes = Horoscope.query.order_by(Horoscope.id.desc()).all()
    return render_template('index.html', horoscopes=horoscopes)

@app.route('/<int:id>')
def index_detail(id):
    horoscope = Horoscope.query.get(id)
    return render_template('index_detail.html', horoscope=horoscope)


@app.route('/add_horoscope', methods=['POST', 'GET'])
@login_required
def adder():
    if request.method == 'POST':
        sign = request.form['title']
        desc = request.form['description']

        horoscope = Horoscope(sign=sign, text=desc)

        try:
            db.session.add(horoscope)
            db.session.commit()
            return redirect('/')
        except:
            return 'При добавлении гороскопа произошла ошибка'
    else:
        return render_template('add_horoscope.html')

@app.route('/stats')
@login_required
def stat():
    messages = Message.query.order_by(Message.date.desc()).all()
    commands = Command.query.order_by(Command.date.desc()).all()

    users_unique = set()
    users = []

    for user in messages:
        if user.chat_id not in users_unique:
            users.append({
                'rname': user.username,
                'rchat_id': user.chat_id
            })
            users_unique.add(user.chat_id)

    for user in commands:
        if user.chat_id not in users_unique:
            users.append({
                'rname': user.username,
                'rchat_id': user.chat_id
            })
            users_unique.add(user.chat_id)

    return render_template('stats.html', users=users)

@app.route('/stats/<int:chat_id>/commands')
def stat_command(chat_id):
    commands = Command.query.order_by(Command.date.desc()).all()

    commands_thchat = []
    for command in commands:
        if command.chat_id == chat_id:
            commands_thchat.append(command)

    return render_template('commands.html', commands_thchat=commands_thchat)

@app.route('/stats/<int:chat_id>/messages')
def stat_message(chat_id):
    messages = Message.query.order_by(Message.date.desc()).all()

    messages_thchat = []
    for message in messages:
        if message.chat_id == chat_id:
            messages_thchat.append(message)

    if (len(messages_thchat) == 0):
        messages_thchat.append(None)

    return render_template('messages.html', messages_thchat=messages_thchat)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        pass1 = request.form['password1']

        user = User.query.filter_by(login=login).first()

        if user:
            bytes_pass = bytes(pass1, 'utf-8')
            if user.password == bcrypt.hashpw(bytes_pass, user.salt):
                login_user(user)
                flash('Авторизация успешно проведена', 'success')
                return render_template('login.html')
            else:
                flash('Проверьте пароль', 'danger')
                return render_template('login.html')
        else:
            flash('Такой пользователь не найден', 'danger')
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/registration', methods=['POST', 'GET'])
def registration():
    role_array = []
    roles = Role.query.all()
    for role in roles:
        role_array.append(role.name)
    if request.method == 'POST':
        login = request.form['login']
        pass1 = request.form['password1']
        pass2 = request.form['password2']
        user_from_db = User.query.filter_by(login=login).first()

        if pass1 == pass2:

            if (user_from_db):
                flash('Данный логин уже занят', 'danger')
                return render_template('reg.html', roles=role_array)

            byte_pass = bytes(pass1, 'utf-8')
            salt = bcrypt.gensalt()
            hash_pass = bcrypt.hashpw(byte_pass, salt)
            action = request.form.get('action')
            if not action:
                role = Role.query.filter_by(name='user').first()
            else:
                role = Role.query.filter_by(name=action).first()
            user = User(login=login, password=hash_pass, salt=salt, role=role)

            try:
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash('Регистрация прошла успешно', 'success')
                return render_template('reg.html', roles=role_array)
            except:
                flash('При регистрации произошла ошибка', 'danger')
                return render_template('reg.html', roles=role_array)
        else:
            flash('Пароли не совпадают', 'danger')
            return render_template('reg.html', roles=role_array)
    else:
        return render_template('reg.html', roles=role_array)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    roles = ['user', 'director', 'manager']
    create_roles(roles)
    app.run()