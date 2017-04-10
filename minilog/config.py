from flask import Flask
import os

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , minilog.py
# Load default config and override config from an environment variable
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='postgresql://felipeskroski@localhost/minilog',
    # SQLALCHEMY_DATABASE_URI='sqlite:////%s' % os.path.join(app.root_path, 'db/minilog.db'),
    # SQLALCHEMY_DATABASE_URI='postgres://qsxmpvuowgydyf:afcb58f63349203db74d27f35cf1fa763c211c6ee6ce733d7284401d570eb598@ec2-107-20-255-96.compute-1.amazonaws.com:5432/d1gmof52s1uoiq',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='A0Zr98j/3yX R~XHH!jmN]LWX/,?RT',
    UPLOAD_FOLDER=os.path.join(app.root_path, 'static/uploads'),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    FACEBOOK = {
        "app_id": "425051767841997",
        "app_secret": "09ccea84402ea63171b7ce4665d1c837"
    }
))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config.from_envvar('MINILOG_SETTINGS', silent=True)
