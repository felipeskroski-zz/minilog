import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, request, session, g, redirect, url_for,
    abort, render_template, flash, escape, jsonify
)
from werkzeug.utils import secure_filename
from models import (
    User, Item, Category, create_hash, check_hash,
    init_db, populate_db, initdb_command, populate_command,
    current_user, db
)

from helpers import (
    SignupForm, LoginForm, ItemForm, CategoryForm
)
from config import app


# ----------------------------
# authentication helpers
# ----------------------------
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
    if form.validate_on_submit():
        category = Category(form.name.data, u.id)
        db.session.add(category)
        db.session.commit()
        flash('New category was successfully posted')
        return redirect(url_for('show_categories'))
    else:
        return render_with_user('category_new.html', form=form)


@app.route('/category/edit/<int:c_id>', methods=['POST', 'GET'])
@login_required
def edit_category(c_id):
    """Updates a category"""
    form = CategoryForm(request.form)
    c = Category.by_id(c_id)
    if form.validate_on_submit():
        db.session.query(Category).\
            filter_by(id=c.id).update({"name": form.name.data})
        db.session.commit()
        flash('Category updated successfully')
        return redirect(url_for('show_categories'))
    else:
        form.name.data = c.name
        return render_with_user('category_new.html', form=form)


@app.route('/category/delete/<int:cat_id>')
@login_required
def delete_category(cat_id):
    """Deletes a category"""
    c = Category.by_id(cat_id)
    items = Item.query.filter_by(category_id=c.id).all()
    if not c.is_author():
        flash('Only the author can delete this category')
        return redirect(url_for('show_categories'))
    else:
        for i in items:
            i.delete_image()
        db.session.delete(c)
        db.session.commit()
        flash('%s category deleted successfully' % c.name)
        return redirect(url_for('show_categories'))


@app.route('/<c_name>')
def show_items(c_name):
    """Show items in a category"""
    c = Category.by_name(c_name)
    return render_with_user('category.html', category=c)

@app.route('/<c_name>/items.json')
def json_category(c_name):
    c = Category.by_name(c_name)
    items = Item.query.filter_by(category_id=c.id).all()
    cat = []
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
    cat.append({
        'id': c.id,
        'category': c.name,
        'author_id' : c.author_id,
        'items': items
    })
    return jsonify(category=cat)


@app.route('/item/new', methods=['GET', 'POST'])
@login_required
def add_item():
    """Creates a new item"""
    form = ItemForm()
    categories = Category.query.order_by('name').all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    u = current_user()
    if form.validate_on_submit():
        f = form.upload.data
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        c_id = form.category_id.data
        c = Category.by_id(c_id)
        i = Item(form.name.data, form.body.data, c_id, u.id, filename)
        db.session.add(i)
        db.session.commit()
        flash('Item created successfully')
        return render_with_user('category.html', category=c)
    else:
        c_id = request.args.get('c_id')
        if c_id:
            form.category_id.data = int(c_id)
        return render_with_user(
            'item_new.html', form=form)


@app.route('/item/edit/<int:i_id>', methods=['POST', 'GET'])
@login_required
def edit_item(i_id):
    """Updates an item"""
    form = ItemForm()
    categories = Category.query.order_by('name').all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    i = Item.by_id(i_id)
    if form.validate_on_submit():
        i.delete_image()
        f = form.upload.data
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.session.query(Item).\
            filter_by(id=i.id).update({
                "name": form.name.data,
                "body": form.body.data,
                "category_id": form.category_id.data,
                "image": filename
            })
        db.session.commit()
        flash('Item updated successfully')
        return redirect(url_for('show_categories'))
    else:
        form.name.data = i.name
        form.body.data = i.body
        form.category_id.data = i.category_id
        return render_with_user('item_new.html', form=form, i=i)

@app.route('/item/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    """Deletes an item"""
    i = Item.by_id(item_id)
    c = i.get_category()
    if i.is_author():
        i.delete_image()
        db.session.delete(i)
        db.session.commit()
        flash('%s deleted successfully' % i.name)
        return render_with_user('category.html', category=c)
    else:
        flash('Only the author can delete this item')
        return render_with_user('category.html', category=c)


@app.route('/<c_name>/<item_name>')
def show_item(c_name, item_name):
    """Display item's details"""
    i = Item.by_name(item_name)
    return render_with_user(
        'item.html', c_name=c_name, item=i)

@app.route('/<c_name>/<item_name>/item.json')
def json_item(c_name, item_name):
    i = Item.by_name(item_name)
    item_json = {
        'id': i.id,
        'name': i.name,
        'description': i.body,
        'category_id': i.category_id,
        'author_id': i.author_id,
        'pub_date': i.pub_date,
    }
    return jsonify(item=item_json)


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
