from flask import Blueprint, jsonify, render_template, request, flash, jsonify, Flask, redirect, url_for
from flask_login import login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from . import db
from .models.users import SystemLevels, Users
from .models.shiftstamp import ShiftStamps, Activities, ShiftStampForm
views = Blueprint('views', __name__)
import datetime

@views.route('/')
def home():    
    return render_template('home.html')

@views.route('/user/<name>')
def user(name):
    return render_template('user.html', user_name=name)

@views.route('/user_list')
def user_list():
    our_users_grabbed = Users.query.order_by(Users.date_added)
    return render_template('/user/user_list.html', our_users=our_users_grabbed)

@views.route('/home')
@login_required
def user_home():
    form = ShiftStampForm()
    choiceMath = [Users.query.get_or_404(current_user.id)]
    form.user.choices = choiceMath
    form.activity.choices = [str(a.activity) for a in Activities.query.order_by()]
    if form.validate_on_submit():
        
        founduser = Users.query.filter_by(id=form.user.data).first()
        shiftstamp = ShiftStamps(user_id=founduser.id, start_time=datetime.combine(form.date.data, datetime.strptime(form.start_time.data, '%H:%M:%S').time()),
            end_time=datetime.combine(form.date.data, datetime.strptime(form.end_time.data, '%H:%M:%S').time()),
            activity=form.activity.data
            )
        shiftstamp.minutes = shiftstamp.end_time - shiftstamp.start_time.total_seconds() / 60
        comparedShift = ShiftStamps.query.filter_by(user_id=shiftstamp.user_id, start_time=shiftstamp.start_time).first()
        if comparedShift:
            flash("This Shift Already Exists.", category='error')
        else:
            db.session.add(shiftstamp)
            db.session.commit()

            form.user.data = ''
            form.date.data = ''
            form.start_time.data = ''
            form.end_time.data = ''
            form.activity.data = ''
            flash("Shift Added Successfully!", category='success')
            return redirect(url_for('views.home'))

    return render_template('/shift/shift_add.html', form=form)

@views.app_errorhandler(404)
def page_not_found(e):
    '''Invalid URL'''
    return render_template("404.html"), 404

@views.app_errorhandler(500)
def internal_server_error(e):
    '''Internal Server Error'''
    return render_template("500.html"), 500

