from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm
from sqlalchemy.orm import relationship
from flask_bootstrap import Bootstrap5
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "medieval app game"

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", 'sqlite:///lists.db')
db = SQLAlchemy()
db.init_app(app)

# Bootstrap needs to be imported.
Bootstrap5(app)



# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


list_items = []
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    lists = relationship("Lists", back_populates='parent_user')


class Lists(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    lists = db.Column(db.String(1000))
    parent_user = relationship("User")

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    result = db.session.execute(db.select(User).where(User.email == request.form.get('email')))
    user = result.scalar()
    if user:
        flash("You've already signed up with that email, log in instead!")
        return redirect(url_for('login'))
    if form.validate_on_submit():
        new_user = User(email=request.form.get('email'),
                        password=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=8),
                        name=request.form.get('name'),

        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login',  methods=["GET", "POST"])
def login():
    form = LoginForm()
    result = db.session.execute(db.select(User).where(User.email == request.form.get('email')))
    user = result.scalar()
    if request.method == "POST":
        if user:

            if check_password_hash(user.password, request.form.get('password')):
                login_user(user)
                return redirect(url_for('home'))

            else:
                flash('Password incorrect, please try again.')
                return render_template("login.html", form=form)
        else:
            flash('That email does not exist, please try again.')
            return render_template("login.html", form=form)
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()

@app.route('/',  methods=['GET','POST'])
def home():

    # current_user.lists = <[List 5]>
    # type(current_user.lists) = <class 'sqlalchemy.orm.collections.InstrumentedList'>

    if request.method == "POST":
        text = request.form['text']
        list_items.append(text)

    return render_template("index.html", current_list=list_items, current_user=current_user)

@app.route('/save_list',  methods=['GET','POST'])
def save_list():
    list_as_string = '/'.join(list_items)
    if current_user.is_authenticated:
        new_list = Lists(lists=list_as_string,
                         parent_user=current_user
                         )
        db.session.add(new_list)
        db.session.commit()
    else:
        flash('You need to login or register to save a list.')
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/new_list',  methods=['GET','POST'])
def new_list():
    list_items.clear()

    return redirect(url_for('home'))

@app.route("/delete/<id>", methods=["GET", "POST"])
def delete(id):
    list_to_delete = db.session.execute(db.select(Lists).where(Lists.id == id)).scalar()
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for('saved_lists'))

@app.route('/saved_lists',  methods=['GET','POST'])
def saved_lists():

    return render_template("saved_lists.html")


if __name__ == '__main__':
    app.run(debug=True)

