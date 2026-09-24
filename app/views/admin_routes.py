from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.views.admin import admin
from app.models.user import User
from app.models.category import Category
from app.forms.admin_forms import AdminUserForm, AdminCategoryForm
from app.utils.decorators import role_required
from app.utils.constants import ROLE_ADMIN

@admin.route('/users', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN)
def list_users():
    form = AdminUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
        elif User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'error')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.list_users'))
            
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin/users.html', users=users, form=form)

@admin.route('/categories', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN)
def list_categories():
    form = AdminCategoryForm()
    if form.validate_on_submit():
        if Category.query.filter_by(name=form.name.data).first():
            flash('Category already exists.', 'error')
        else:
            category = Category(
                name=form.name.data,
                description=form.description.data
            )
            db.session.add(category)
            db.session.commit()
            flash('Category created successfully.', 'success')
            return redirect(url_for('admin.list_categories'))
            
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories, form=form)

