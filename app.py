from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime
import subprocess

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
db = SQLAlchemy(app)
app.app_context().push()

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

@app.route('/')
def index():
    horoscopes = Horoscope.query.order_by(Horoscope.id.desc()).all()
    return render_template('index.html', horoscopes=horoscopes)

@app.route('/<int:id>')
def index_detail(id):
    horoscope = Horoscope.query.get(id)
    return render_template('index_detail.html', horoscope=horoscope)


@app.route('/add_horoscope', methods=['POST', 'GET'])
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

    return render_template('messages.html', messages_thchat=messages_thchat)

if __name__ == '__main__':
    app.run()