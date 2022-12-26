from flask import Blueprint, render_template

auth = Blueprint('auth', __name__)

# if user not logged in and visits index /, redirect to /auth
@auth.route('/auth')
def auth_page():
    return "<p>This is Auth</p>"
