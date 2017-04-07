import os
from datetime import datetime
from functools import wraps
from bcrypt import hashpw, gensalt
from flask import (
    Flask, request, session, g, redirect, url_for,
    abort, render_template, flash, escape, jsonify
)
from wtforms import (
    Form, BooleanField, StringField, PasswordField, SelectField, HiddenField,
    TextAreaField, validators
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , minilog.py
# Load default config and override config from an environment variable
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='sqlite:////%s' % os.path.join(app.root_path, 'minilog.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    SECRET_KEY='A0Zr98j/3yX R~XHH!jmN]LWX/,?RT',
))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config.from_envvar('MINILOG_SETTINGS', silent=True)
db = SQLAlchemy(app)


class User(db.Model):
    """
    Creates user model
    name = the user name
    email = user email
    password = hashed password
    """
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
        return User.query.filter_by(id=uid).first()

    @classmethod
    def by_email(cls, email):
        """Gets user by email"""
        return User.query.filter_by(email=email).first()


class Item(db.Model):
    """
    Creates item model
    name = the item's name
    body = item's description
    pub_date = creation's date
    author_id = the id of the User who created the Item
    category_id = the category in wich the item belongs
    """
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

    def __init__(self, name, body, category_id, author_id, pub_date=None):
        self.name = name
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.category_id = category_id
        self.author_id = author_id

    def __repr__(self):
        return '<Post %r>' % self.title

    @classmethod
    def by_id(cls, i_id):
        """Gets Item by id"""
        return Item.query.filter_by(id=i_id).first()

    @classmethod
    def by_name(cls, i_name):
        """Gets item by name"""
        return Item.query.filter_by(name=i_name).first()

    def is_author(self):
        """Check if current user is this item's author"""
        if not current_user():
            return False
        return self.author_id == current_user().id

    def get_category(self):
        """Gets this item's category"""
        return Category.query.filter_by(id=self.category_id).first()


class Category(db.Model):
    """Creates category model plus methods"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship(
        'User', backref=db.backref('category', lazy='dynamic'))
    # Whenever you delete a category delete all it's children items
    items = db.relationship("Item", cascade="delete")

    def __init__(self, name, author_id):
        self.name = name
        self.author_id = author_id

    def __repr__(self):
        return '<Category %r>' % self.name

    @classmethod
    def by_id(cls, c_id):
        """Gets Category by id"""
        return Category.query.filter_by(id=c_id).first()

    @classmethod
    def by_name(cls, c_name):
        """Gets Category by name"""
        return Category.query.filter_by(name=c_name).first()

    def is_author(self):
        """Checks if the current user is the author"""
        if not current_user():
            return False
        return self.author_id == current_user().id

    def get_items(self):
        """Gets all items in this category"""
        return Item.query.filter_by(category_id=self.id).all()


# ----------------------------
# Database config
# ----------------------------
def init_db():
    """Install fresh copy of database"""
    db.drop_all()
    db.create_all()


def populate_db():
    """Loads mock data into de db"""
    # create dummy user
    user = User('admin', 'admin@example.com', 'password')
    db.session.add(user)
    db.session.commit()
    # create dummy categories
    category1 = Category('Basketball', user.id)
    category2 = Category('Camping', user.id)
    db.session.add(category1)
    db.session.add(category2)
    db.session.commit()
    # create dummy items
    item1 = Item(
        'Ball', 'Perfectly round and bouncier than ever',
        category1.id, user.id)
    item2 = Item(
        'Shoes', 'Super light and comfortable',
        category1.id, user.id)
    item3 = Item(
        'Tent', 'Good shelter even on the rainy days',
        category2.id, user.id)
    db.session.add(item1)
    db.session.add(item2)
    db.session.add(item3)
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
    """Create password hash to be stored in the database"""
    return hashpw(plaintext_password, gensalt())


def check_hash(password_attempt, hashed):
    """Checks the password hash against a test"""
    return hashpw(password_attempt, hashed) == hashed


def current_user():
    """Returns the logged user"""
    if 'email' not in session:
        return False
    return User.by_email(escape(session['email']))


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('You need to login to change the content')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

def render_with_user(*args, **kwargs):
    u = current_user()
    return render_template(user=u, *args, **kwargs)
# ----------------------------
# Forms
# ----------------------------


class SignupForm(Form):
    """Sets form for signup"""
    name = StringField('Name', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')


class LoginForm(Form):
    """Sets form for login"""
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired()
    ])


class CategoryForm(Form):
    """Sets form for category creation"""
    name = StringField('Name', [validators.DataRequired()])


class ItemForm(Form):
    """Sets form for item creation"""
    name = StringField('Name', [validators.DataRequired()])
    body = TextAreaField('Description')
    category_id = SelectField('Category', coerce=int)

# ----------------------------
# views
# ----------------------------


@app.route('/')
def show_categories():
    """Show all categories and latest items"""
    categories = Category.query.all()
    items = Item.query.order_by('pub_date desc').limit(10).all()
    return render_with_user(
        'categories.html', categories=categories, items=items)



@app.route('/catalog.json')
def json_categories():
    categories = Category.query.all()
    items = Item.query.limit(10).all()
    names = []
    for c in categories:
        items=[]
        for i in c.get_items():
            items.append({
                'id': i.id,
                'name': i.name,
                'description': i.body,
                'category_id': i.category_id,
                'author_id': i.author_id,
                'pub_date': i.pub_date,
            })
        names.append({
            'id': c.id,
            'category': c.name,
            'author_id' : c.author_id,
            'items': items
        })
    return jsonify(categories=names)


@app.route('/category/new', methods=['POST', 'GET'])
@login_required
def add_category():
    """Creates a new category"""
    form = CategoryForm(request.form)
    error = None
    u = current_user()
    if request.method == 'POST' and form.validate():
        category = Category(form.name.data, u.id)
        db.session.add(category)
        db.session.commit()
        flash('New category was successfully posted')
        return redirect(url_for('show_categories'))
    else:
        return render_with_user('category_new.html', form=form)



@app.route('/category/delete/<int:cat_id>')
# TODO when removing a category also remove the items
@login_required
def delete_category(cat_id):
    """Deletes a category"""
    cat = Category.by_id(cat_id)
    if not cat.is_author():
        flash('Only the author can delete this category')
        return redirect(url_for('show_categories'))
    else:
        db.session.delete(cat)
        db.session.commit()
        flash('%s category deleted successfully' % cat.name)
        return redirect(url_for('show_categories'))


@app.route('/<c_name>')
def show_items(c_name):
    """Show items in a category"""
    c = Category.by_name(c_name)
    return render_with_user('category.html', category=c)


@app.route('/item/new', methods=['GET', 'POST'])
@login_required
def add_item():
    """Creates a new item"""
    form = ItemForm(request.form)
    categories = Category.query.order_by('name').all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    u = current_user()
    if request.method == 'POST' and form.validate():
        c_id = form.category_id.data
        c = Category.by_id(c_id)
        item = Item(form.name.data, form.body.data, c_id, u.id)
        db.session.add(item)
        db.session.commit()
        flash('Item created successfully')
        return render_with_user('category.html', category=c)
    else:
        c_id = request.args.get('c_id')
        if c_id:
            form.category_id.data = int(c_id)
        return render_with_user(
            'item_new.html', form=form)


@app.route('/item/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    """Deletes an item"""
    item = Item.by_id(item_id)
    c = item.get_category()
    if item.is_author():
        db.session.delete(item)
        db.session.commit()
        flash('%s deleted successfully' % item.name)
        return render_with_user('category.html', category=c)
    else:
        flash('Only the author can delete this item')
        return render_with_user('category.html', category=c)


@app.route('/<c_name>/<item_name>')
def show_item(c_name, item_name):
    """Display item's details"""
    item = Item.by_name(item_name)
    return render_with_user(
        'item.html', c_name=c_name, item=item)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Creates a new user"""
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(form.name.data, form.email.data,
                    form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks for registering')
        return redirect(url_for('show_categories'))
    return render_with_user('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
# TODO Check if user already exists
def login():
    """Logs the user in"""
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        u = User.by_email(form.email.data)
        if u and check_hash(str(form.password.data), str(u.password)):
            session['email'] = request.form['email']
            flash('You were logged in')
            return redirect(url_for('show_categories'))
        else:
            error = "User not valid"
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Logs the user out"""
    session.pop('email', None)
    flash('You were logged out')
    return redirect(url_for('show_categories'))
