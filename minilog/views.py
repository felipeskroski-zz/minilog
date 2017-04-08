from functools import wraps
from wtforms import (
    Form, BooleanField, StringField, PasswordField, SelectField, HiddenField,
    TextAreaField, validators
)
from flask import (
    Flask, request, session, g, redirect, url_for,
    abort, render_template, flash, escape, jsonify
)
from models import (
    User, Item, Category, create_hash, check_hash,
    init_db, populate_db, initdb_command, populate_command,
    current_user
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


@app.route('/category/edit/<int:c_id>', methods=['POST', 'GET'])
@login_required
def edit_category(c_id):
    """Updates a category"""
    form = CategoryForm(request.form)
    c = Category.by_id(c_id)
    if request.method == 'POST' and form.validate():
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


@app.route('/item/edit/<int:i_id>', methods=['POST', 'GET'])
@login_required
def edit_item(i_id):
    """Updates an item"""
    form = ItemForm(request.form)
    categories = Category.query.order_by('name').all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    i = Item.by_id(i_id)
    if request.method == 'POST' and form.validate():
        db.session.query(Item).\
            filter_by(id=i.id).update({
                "name": form.name.data,
                "body": form.body.data,
                "category_id": form.category_id.data
            })
        db.session.commit()
        flash('Item updated successfully')
        return redirect(url_for('show_categories'))
    else:
        form.name.data = i.name
        form.body.data = i.body
        form.category_id.data = i.category_id
        return render_with_user('item_new.html', form=form)

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
