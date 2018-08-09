#!/usr/bin/env python
# encoding: utf-8

from flasgger import Swagger
from flask import Flask, Response, abort, g, jsonify, redirect, render_template, request, session, url_for

from flask_login import LoginManager, login_required, login_user, logout_user
from flask_wtf import FlaskForm

from google.cloud import storage

from model import User, load_users

from os import path, environ

from urllib.parse import urlparse, urljoin

from wtforms import BooleanField, PasswordField, SubmitField, StringField
from wtforms.validators import Email, InputRequired, Length
from wtforms.widgets import PasswordInput

import json
import sys


######################################################################
## simple app

basedir = path.abspath(path.dirname(__file__))

# Flask config
APP = Flask(__name__, static_folder="static")
APP.config.from_envvar("FLASK_CONFIG")

# Flask-Login
LOGIN_MANAGER = LoginManager()
LOGIN_MANAGER.init_app(APP)
LOGIN_MANAGER.login_message = "complete your login to access that page"
LOGIN_MANAGER.login_view = "auth_login"
LOGIN_MANAGER.session_protection = "strong"

# overly-simplistic model
load_users("users.json")


######################################################################
## OpenAPI support

FLASK_BUILD = environ.get("FLASK_BUILD", "unknown build")

API_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Computable.io minimal cloud storage API",
        "description": "Computable.io minimal cloud storage API",
        "contact": {
            "responsibleOrganization": "Computable.io",
            "responsibleDeveloper": "Jane Q. Haquer",
            "email": "hello@computable.io"
        },
        "termsOfService": "https://computable.io/",
        "version": FLASK_BUILD
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "externalDocs": {
        "description": "Computable.io minimal cloud storage API docs",
        "url": "https://github.com/derwenai/stor"
    }
}

SWAGGER = Swagger(APP, template=API_TEMPLATE)


######################################################################
## API routes

@APP.route("/api/v1/info")
def get_build_info ():
    """
    get build info
    ---
    tags:
      - UI load
    description: 'get the build info for the code used in this API'
    produces:
      - application/json
    responses:
      '200':
        description: Git tag for the code
    """
    return jsonify({
        "code": FLASK_BUILD
    })


@APP.route("/auth/get")
@login_required
def page_get_file ():
    bucket_name = APP.config["DATA_BUCKET"]
    file_path = request.args.get("file")
    print(bucket_name, file_path)

    client = storage.Client()
    bucket = client.get_bucket(bucket_name)

    blob = bucket.get_blob(file_path)
    content = blob.download_as_string()

    return Response(content, mimetype="text/plain")


######################################################################
## authentication helpers

class LoginForm (FlaskForm):
    ## http://flask-wtf.readthedocs.io/
    ## https://github.com/marcelomd/flask-wtf-login-example

    email = StringField(
        "email",
        validators=[
            InputRequired(message="please enter your email address"), 
            Email(message="this field requires a valid email address"),
            Length(max=255),
            ]
        )

    password = PasswordField(
        "password",
        widget=PasswordInput(hide_value=False),
        validators=[
            InputRequired(message="please enter the password for this account"),
            Length(max=255),
            ]
        )

    #remember_me = BooleanField("remember me")
    submit = SubmitField("login")


def is_safe_url (target):
    ## http://flask.pocoo.org/snippets/62/
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    schemes = ("http", "https",)

    return test_url.scheme in schemes and ref_url.netloc == test_url.netloc


@APP.before_request
def before_request ():
    """load the authenticated user, if any"""
    try:
        g.user = current_user
    except NameError:
        pass


@LOGIN_MANAGER.user_loader
def load_user (userid):
    """callback to reload a User object"""
    return User.from_id(userid)


######################################################################
## authentication routes

@APP.route("/auth/login", methods=["GET", "POST"])
def auth_login ():
    """somewhere to login"""
    form = LoginForm()

    if form.validate_on_submit():
        user = User.from_email(form.email.data)

        if not user or not user.check_password(form.password.data):
            return abort(401)
        else:
            login_user(user, remember=True)
            session.modified = True

            next = request.args.get("next")

            if not is_safe_url(next):
                return abort(400)
            else:
                return redirect(next or url_for("home"))
    else:
        return render_template("login.html", form=form)


@APP.route("/auth/logout")
@login_required
def auth_logout ():
    """somewhere to logout"""
    logout_user()
    session.modified = True
    return redirect(url_for("home"))


@APP.errorhandler(401)
def login_failed (e):
    """handle failed login"""
    return render_template("error.html", error=str(e))
    

######################################################################
## app routes

# an unprotected url
@APP.route("/")
def home ():
    return render_template("index.html")


######################################################################
## main

if __name__ == "__main__":
    APP.run(host="0.0.0.0", debug=True)
