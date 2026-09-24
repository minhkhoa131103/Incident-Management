from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.views.auth import auth
from app.models.user import User
from app.forms.auth_forms import LoginForm
from app.utils.constants import ROLE_REPORTER

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('incidents.list_incidents'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                if user.role == ROLE_REPORTER:
                    next_page = url_for('incidents.list_incidents')
                else:
                    next_page = url_for('dashboard.index')
            return redirect(next_page)
        flash('Invalid username or password.', 'error')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
