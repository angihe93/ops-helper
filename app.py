from flask import Flask, render_template, flash, redirect, url_for
from views.auth import auth
from views.calendar import calendar
from views.main_site_ops import main_site_ops
from flask_bcrypt import Bcrypt, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
import os

class User(UserMixin):
    id = 1
    username = 'hubbub' 
    def __repr__(self):
        return '<User %r>' % self.username

admin_user = User()
admin_email = os.environ.get('ADMIN_EMAIL')
admin_password = os.environb[b'ADMIN_PASSWORD']

class login_form(FlaskForm):
    email = StringField() 
    pwd = PasswordField()
    username = StringField()


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

bcrypt = Bcrypt()
bcrypt.init_app(app)

app.register_blueprint(auth)
app.register_blueprint(calendar)
app.register_blueprint(main_site_ops)

@app.route("/")
def index():
    # if admin_user.is_authenticated:
    #     return redirect(url_for('calendar.upcoming_tasks'))
    return redirect(url_for('login'))

@app.route("/login", methods=("GET", "POST"))
def login():
    # print('admin_user.is_authenticated',admin_user.is_authenticated)
    # if admin_user.is_authenticated:
    #     return redirect(url_for('calendar.upcoming_tasks'))

    form = login_form()

    if form.validate_on_submit():
        try:
            user = admin_user
            if form.email.data==admin_email and check_password_hash(admin_password, form.pwd.data):
            # if form.pwd.data==admin_password:
                login_user(user)
                return redirect(url_for('calendar.upcoming_tasks'))
            else:
                flash("Invalid username or password") #, "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
    # return f"you've been logged out. <a href={url_for('login')}>log in</a>"

@login_manager.user_loader
def load_user(user_id):
    return admin_user

# @app.route('/clear')
# def clear_credentials():
#     # print('clear:')
#     # print('flask.session',flask.session)
#     if 'credentials' in flask.session:
#         del flask.session['credentials']
#         del flask.session['state']
#         # print('flask.session',flask.session)
#     return ('Credentials have been cleared.<br><br> <a href="login">login</a>')  # +
#     # print_index_table())

if __name__ == "__main__":
    app.run(debug=True, ssl_context='adhoc')
