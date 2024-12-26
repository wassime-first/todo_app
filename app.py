from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
URI = os.getenv("URI")

date_now = datetime.datetime.now()
date_now = date_now.strftime("%Y-%m-%d")

yeastearday_date = datetime.date.today() - datetime.timedelta(days=1)
yeastearday_date = yeastearday_date.strftime("%Y-%m-%d")

app = Flask(__name__)
app.config['SECRET_KEY'] = (SECRET_KEY)

""" database """
app.config['SQLALCHEMY_DATABASE_URI'] = URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
''' bootstrap'''
bootstrap = Bootstrap(app)

""" login manager """
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

""" user loader """


@login_manager.user_loader
def load_user(user_id):
    return UserToDo.query.get(int(user_id))


""" user table """


class UserToDo(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    tasks = db.relationship("Task", back_populates="user", cascade="all, delete, save-update")


""" tasks table """


class Task(UserMixin, db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    complete = db.Column(db.Integer, nullable=False, default=0)
    user = db.relationship("UserToDO", back_populates="tasks")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)


""" register form """


class RegisterForm(FlaskForm):
    name = StringField("Name")
    email = EmailField("Email")
    password = PasswordField("Password")
    submit = SubmitField("Sign Up")


""" login form """


class LoginForm(FlaskForm):
    email = EmailField("Email")
    password = PasswordField("Password")
    submit = SubmitField("Login")


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", user=current_user, logged_in=current_user.is_authenticated)


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password, salt_length=8)
        new_user = UserToDo(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("tasks"))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get("email")
        password = request.form.get("password")
        user = UserToDo.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("tasks"))
        else:
            return redirect(url_for("login"))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/tasks", methods=["POST", "GET"])
@login_required
def tasks():
    global hour_now, date_now, yeastearday_date
    now_tasks = Task.query.filter_by(user_id=current_user.id).filter_by(date=date_now).all()
    previous_day_tasks = Task.query.filter_by(user_id=current_user.id).filter_by(date=yeastearday_date).all()
    today_tasks = []
    today_tasks.append(now_tasks)
    if previous_day_tasks:
        for task in previous_day_tasks:
            if task.complete == 0:
                task.date = date_now
                db.session.commit()
                today_tasks.append(task)

            else:
                task.complete = 0
                task.date = date_now
                db.session.commit()
                tasks.append(task)
    else:
        today_tasks = now_tasks

    return render_template("tasks.html", tasks=today_tasks, user=current_user, logged_in=current_user.is_authenticated)


@app.route("/add", methods=["POST", "GET"])
def add():
    if request.method == "POST":
        title = request.form.get("title")
        date = date_now
        new_task = Task(title=title, date=date, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("tasks"))
    return render_template("add.html", logged_in=current_user.is_authenticated)


@app.route("/delete/<int:id>", methods=["POST", "GET"])
def delete(id):
    task_to_delete = Task.query.get(id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("tasks"))


@app.route("/update/<int:id>", methods=["POST", "GET"])
def edit(id):
    task_to_update = Task.query.get(id)
    if request.method == "POST":
        title = request.form.get("title")
        task_to_update.title = title
        db.session.commit()
        return redirect(url_for("tasks"))
    return render_template("update.html", task=task_to_update, logged_in=current_user.is_authenticated)


@app.route("/complete/<int:id>", methods=["POST", "GET"])
def complete(id):
    task_to_complete = Task.query.get(id)
    task_to_complete.complete = 1
    db.session.commit()
    return redirect(url_for("tasks"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
