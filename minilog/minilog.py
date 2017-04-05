import os
from bcrypt import hashpw, gensalt
from flask import (
    Flask, request, session, g, redirect, url_for,
    abort, render_template, flash, escape
)
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , minilog.py
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'minilog.db'),
    SQLALCHEMY_DATABASE_URI='sqlite:////%s' % os.path.join(app.root_path, 'minilog.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    SECRET_KEY='A0Zr98j/3yX R~XHH!jmN]LWX/,?RT',
    USERNAME='admin',
    PASSWORD='password'
))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config.from_envvar('MINILOG_SETTINGS', silent=True)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(80))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = create_hash(str(password))

    def __repr__(self):
        return '<User %r>' % self.name

    @classmethod
    def by_id(cls, uid):
        """Gets user by id"""
        return User.get_by_id(uid)

    @classmethod
    def by_email(cls, email):
        """Gets user by name"""
        u = User.query.filter_by(email= email).first()
        return u


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship(
        'User', backref=db.backref('item', lazy='dynamic'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(
        'Category', backref=db.backref('item', lazy='dynamic'))

    def __init__(self, name, body, category, author, pub_date=None):
        self.name = name
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.category = category
        self.author = author

    def __repr__(self):
        return '<Post %r>' % self.title


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship(
        'User', backref=db.backref('category', lazy='dynamic'))

    def __init__(self, name, author_id):
        self.name = name
        self.author_id = author_id

    def __repr__(self):
        return '<Category %r>' % self.name

# ----------------------------
# Database config
# ----------------------------

def init_db():
    db.drop_all()
    db.create_all()


def populate_db():
    # create dummy user
    user = User('admin', 'admin@example.com', 'password')
    db.session.add(user)
    db.session.commit()
    # create dummy categories
    category1 = Category('Sports', user.id)
    category2 = Category('Clothing', user.id)
    db.session.add(category1)
    db.session.add(category2)
    db.session.commit()



@app.cli.command('initdb')
def initdb_command():
    """Terminal command: Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.cli.command('populatedb')
def populate_command():
    """Terminal command: Adds mock data to the database."""
    populate_db()
    print('Mock data added the database.')


# ----------------------------
# authentication helpers
# ----------------------------
def create_hash(plaintext_password):
    return hashpw(plaintext_password, gensalt())


def check_hash(password_attempt, hashed):
    return hashpw(password_attempt, hashed) == hashed

# ----------------------------
# Forms
# ----------------------------

class SignupForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')


# ----------------------------
# views
# ----------------------------

@app.route('/')
def show_categories():
    categories = Category.query.all()
    if 'email' in session:
        u = User.by_email(escape(session['email']))
        return render_template(
            'show_categories.html', categories=categories, user=u)
    return render_template('show_categories.html', categories=categories)


@app.route('/newcategory', methods=['POST', 'GET'])
def add_category():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        if name:
            user = User.query.first_or_404()
            category = Category(name, user.id)
            db.session.add(category)
            db.session.commit()
            flash('New category was successfully posted')
            return redirect(url_for('show_categories'))
        else:
            error = 'Name cannot be empty'
    return render_template('new_category.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(form.name.data, form.email.data,
                    form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks for registering')
        return redirect(url_for('show_categories'))
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        u = User.by_email(email)
        if u and check_hash(str(password), str(u.password)):
            session['email'] = request.form['email']
            flash('You were logged in')
            return redirect(url_for('show_categories'))
        else:
            error = "User not valid"
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You were logged out')
    return redirect(url_for('show_categories'))
