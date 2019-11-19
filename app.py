# app.py
import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

APP_ROOT = os.path.dirname(os.path.realpath(__file__))
DEBUG = False

class CustomFlask(Flask):
  jinja_options = Flask.jinja_options.copy()
  jinja_options.update(dict(
    block_start_string='(%',
    block_end_string='%)',
    variable_start_string='((',
    variable_end_string='))',
    comment_start_string='(#',
    comment_end_string='#)',
  ))

app = CustomFlask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1, x_for=1, x_host=1)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["500 per hour"]
)

app.config.from_object(__name__)
UPLOAD_FOLDER = './tempuploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

try:
    os.mkdir(UPLOAD_FOLDER)
except:
    print("cannot make folder", UPLOAD_FOLDER)
