import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, CD, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from flask_mail import Mail, Message

# Ensure instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

app = Flask(__name__)
app.secret_key = 'Riansh@819'  # Replace with something unpredictable in production!
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 📧 Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rohinivelagapudi@gmail.com'
app.config['MAIL_PASSWORD'] = 'zjcw dlee ajgu fcvv'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@cdtracker.com'

mail = Mail(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def calculate_interest(cd):
    days_elapsed = (date.today() - cd.start_date).days
    years = max(days_elapsed / 365.0, 0)
    interest = cd.amount * (cd.interest_rate / 100) * years
    return round(interest, 2), round(cd.amount + interest, 2)

@app.route('/')
@login_required
def index():
    cds = CD.query.filter_by(user_id=current_user.id).order_by(CD.maturity_date).all()
    enriched_cds = []
    for cd in cds:
        interest, total_value = calculate_interest(cd)
        enriched_cds.append({
            'id': cd.id,
            'bank_name': cd.bank_name,
            'amount': cd.amount,
            'interest_rate': cd.interest_rate,
            'start_date': cd.start_date,
            'maturity_date': cd.maturity_date,
            'notes': cd.notes,
            'interest': interest,
            'total_value': total_value
        })
    return render_template('index.html', cds=enriched_cds)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        cd = CD(
            bank_name=request.form['bank_name'],
            amount=float(request.form['amount']),
            interest_rate=float(request.form['interest_rate']),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d'),
            maturity_date=datetime.strptime(request.form['maturity_date'], '%Y-%m-%d'),
            notes=request.form.get('notes', ''),
            user_id=current_user.id
        )
        db.session.add(cd)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_cd.html')

@app.route('/update/<int:cd_id>', methods=['POST'])
@login_required
def update(cd_id):
    cd = CD.query.filter_by(id=cd_id, user_id=current_user.id).first_or_404()
    cd.bank_name = request.form['bank_name']
    cd.amount = float(request.form['amount'])
    cd.interest_rate = float(request.form['interest_rate'])
    cd.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    cd.maturity_date = datetime.strptime(request.form['maturity_date'], '%Y-%m-%d')
    cd.notes = request.form.get('notes', '')
    db.session.commit()
    return '', 204

@app.route('/delete/<int:cd_id>', methods=['POST'])
@login_required
def delete(cd_id):
    cd = CD.query.filter_by(id=cd_id, user_id=current_user.id).first_or_404()
    db.session.delete(cd)
    db.session.commit()
    return '', 204

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        new_password = request.form['new_password']
        user = User.query.filter_by(username=username, email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            send_password_change_email(user.email, user.username)
            flash('Password updated! Please check your email.')
            return redirect(url_for('login'))
        else:
            flash('Username or email not found')
    return render_template('forgotpassword.html')

def send_password_change_email(email, username):
    msg = Message(
        subject="Your CD Tracker Password Was Changed",
        recipients=[email]
    )
    msg.body = f"""
Hi {username},

Your password was recently changed on CD Tracker.

If you made this change, you can ignore this email.

If you did NOT change your password, please reply to this email with "NO" immediately. We will lock your account to protect your data.

Thank you,
CD Tracker Security Team
"""
    mail.send(msg)

@app.route('/report_fraud', methods=['POST'])
def report_fraud():
    username = request.form['username']
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_locked = True
        db.session.commit()
        flash('Your account has been locked. Please contact support to reset your password.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)