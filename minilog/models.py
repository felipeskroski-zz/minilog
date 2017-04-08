import os
from datetime import datetime
from bcrypt import hashpw, gensalt
from flask import (
    Flask, session, g, escape
)
from flask_sqlalchemy import SQLAlchemy
from helpers import check_hash, create_hash
from config import app

db = SQLAlchemy(app)

def current_user():
    """Returns the logged user"""
    if 'email' not in session:
        return False
    return User.by_email(escape(session['email']))

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
