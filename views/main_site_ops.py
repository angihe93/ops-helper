from flask import Blueprint, render_template

main_site_ops = Blueprint('main_site_ops', __name__)

@main_site_ops.route('/main-site-ops')
def show_main_site_ops():
    return "<a href='calendar'>Calendar</a><p>This is Main Site Ops"
