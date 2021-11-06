# Flask
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import g
from flask import flash

# Form
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import TextAreaField
from wtforms import HiddenField
from wtforms.validators import InputRequired

# Database
from .models import db
from .models import Article
from .models import User

import os
from flask_bootstrap import Bootstrap



flask_app = Flask(__name__)
flask_app.config.from_pyfile("default.py")
bootstrap = Bootstrap(flask_app)
 

if "MDBLOG_CONFIG" in os.environ:
    flask_app.config.from_envvar("MDBLOG_CONFIG")

db.init_app(flask_app)

# ERROR HANDELING
@flask_app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.jinja"), 500

@flask_app.errorhandler(404)
def internal_server_error(error):
    return render_template("404.jinja"), 404

## FORMS
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])

class ArticleForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    content = TextAreaField("Content")
    html_render = HiddenField()

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old Password", validators=[InputRequired()])
    new_password = PasswordField("New Password", validators=[InputRequired()])

## CONTROLLERS
@flask_app.route("/")
def view_welcome_page():
    return render_template("welcome_page.jinja")

@flask_app.route("/about/")
def view_about():
    return render_template("about.jinja")

@flask_app.route("/admin/")
def view_admin():
    if "logged" not in session:
        flash("You must be logged in", "alert-danger")
        return redirect(url_for("view_login"))
    return render_template("admin.jinja")

### ARTICLES
@flask_app.route("/articles/", methods=["GET"])
def view_articles():
    page = request.args.get("page", 1, type=int)
    paginate = Article.query.order_by(Article.id.desc()).paginate(page, 5, False)
    return render_template("articles.jinja",
            articles=paginate.items,
            paginate=paginate)


@flask_app.route("/articles/new/", methods=["GET"])
def view_add_article():
    if "logged" not in session:
        return redirect(url_for("view_login"))

    form = ArticleForm()
    return render_template("article_editor.jinja", form=form)

@flask_app.route("/articles/", methods=["POST"])
def add_article():
    if "logged" not in session:
        return redirect(url_for("view_login"))

    add_form = ArticleForm(request.form)
    if add_form.validate():
        new_article = Article(
                title = add_form.title.data,
                content = add_form.content.data,
                html_render = add_form.html_render.data)
        db.session.add(new_article)
        db.session.commit()
        flash("Article was saved", "alert-success")
        return redirect(url_for("view_articles"))
    else:
        for error in add_form.errors:
            flash("{} is required".format(error), "alert-danger")
        return render_template("article_editor.jinja", form=add_form)

@flask_app.route("/articles/<int:art_id>/")
def view_article(art_id):
    article = Article.query.filter_by(id=art_id).first()
    if article:
        return render_template("article.jinja", article=article)
    return render_template("article_not_found.jinja", art_id=art_id)

@flask_app.route("/articles/<int:art_id>/edit/", methods=["GET"])
def view_article_editor(art_id):
    if "logged" not in session:
        return redirect(url_for("view_login"))
    article = Article.query.filter_by(id=art_id).first()
    if article:
        form = ArticleForm()
        form.title.data = article.title
        form.content.data = article.content
        return render_template("article_editor.jinja", form=form, article=article)
    return render_template("article_not_found.jinja", art_id=art_id)


@flask_app.route("/articles/<int:art_id>/", methods=["POST"])
def edit_article(art_id):
    if "logged" not in session:
        return redirect(url_for("view_login"))
    article = Article.query.filter_by(id=art_id).first()
    if article:
        edit_form = ArticleForm(request.form)
        if edit_form.validate():
            article.title = edit_form.title.data
            article.content = edit_form.content.data
            db.session.add(article)
            db.session.commit()
            flash("Edit saved", "alert-success")
            return redirect(url_for("view_article", art_id=art_id))
        else:
            for error in login_form.errors:
                flash("{} is missing".format(error), "alert-danger")
            return redirect(url_for("view_login"))

@flask_app.route("/login/", methods=["GET"])
def view_login():
    login_form = LoginForm()
    return render_template("login.jinja", form=login_form)

@flask_app.route("/login/", methods=["POST"])
def login_user():
    login_form = LoginForm(request.form)
    if login_form.validate():
        user = User.query.filter_by(username = login_form.username.data).first()
        if user and user.check_password(login_form.password.data):
            session["logged"] = user.username
            flash("Login successful", "alert-success")
            return redirect(url_for("view_admin"))
        else:
            flash("Invalid credentials", "alert-danger")
            return render_template("login.jinja", form=login_form)
    else:
        for error in login_form.errors:
            flash("{} is missing".format(error), "alert-danger")
        return redirect(url_for("view_login"))

@flask_app.route("/changepassword/", methods=["GET"])
def view_change_password():
    if "logged" not in session:
        return redirect(url_for("view_login"))
    form = ChangePasswordForm()
    return render_template("change_password.jinja", form=form)

@flask_app.route("/changepassword/", methods=["POST"])
def change_password():
    if "logged" not in session:
        return redirect(url_for("view_login"))
    form = ChangePasswordForm(request.form)
    if form.validate():
        user = User.query.filter_by(username = session["logged"]).first()
        if user and user.check_password(form.old_password.data):
            user.set_password(form.new_password.data)
            db.session.add(user)
            db.session.commit()
            flash("Password changed!", "alert-success")
            return redirect(url_for("view_admin"))
        else:
            flash("Invalid credentials", "alert-danger")
            return render_template("change_password.jinja", form=form)
    else:
        for error in form.errors:
            flash("{} is missing".format(error), "alert-danger")
        return render_template("change_password.jinja", form=form)

@flask_app.route("/logout/", methods=["POST"])
def logout_user():
    session.pop("logged")
    flash("Logout successful", "alert-success")
    return redirect(url_for("view_welcome_page"))


## CLI COMMAND
def init_db(app):
    with app.app_context():
        db.create_all()
        print("database inicialized")

        default_user = User(username="admin")
        default_user.set_password("admin")

        db.session.add(default_user)
        db.session.commit()
        print("default user was created")