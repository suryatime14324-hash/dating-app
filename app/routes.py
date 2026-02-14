from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import json
import os

from app import db
from app.models import User, Profile, Like, Match, Message

main = Blueprint('main', __name__)


# ================= HOME =================

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.discover'))
    return render_template('index.html')


# ================= AUTH =================

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.discover'))

        flash("Invalid credentials", "error")

    return render_template("login.html")


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return redirect(url_for('main.register'))

        user = User(email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('main.edit_profile'))

    return render_template("register.html")


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# ================= PROFILE =================

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = current_user.profile

    if request.method == 'POST':
        if not profile:
            profile = Profile(user_id=current_user.id)
            db.session.add(profile)

        profile.name = request.form.get('name')
        profile.age = request.form.get('age', type=int)
        profile.bio = request.form.get('bio')

        db.session.commit()
        return redirect(url_for('main.profile'))

    return render_template('edit_profile.html', profile=profile)


# ================= DISCOVER =================

@main.route('/discover')
@login_required
def discover():

    users = User.query.join(Profile).filter(
        User.id != current_user.id
    ).all()

    return render_template('discover.html', users=users)


# ================= VIEW USER =================

@main.route('/user/<user_id>')
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user=user)


# ================= LIKE =================

@main.route('/like/<user_id>', methods=['POST'])
@login_required
def like_user(user_id):

    if Like.query.filter_by(liker_id=current_user.id, liked_id=user_id).first():
        return jsonify({'error': 'Already liked'}), 400

    db.session.add(Like(liker_id=current_user.id, liked_id=user_id))

    liked_back = Like.query.filter_by(
        liker_id=user_id,
        liked_id=current_user.id
    ).first()

    is_match = False

    if liked_back:
        db.session.add(Match(
            user1_id=current_user.id,
            user2_id=user_id,
            matched_at=datetime.utcnow()
        ))
        is_match = True

    db.session.commit()

    return jsonify({"success": True, "is_match": is_match})


# ================= MATCHES =================

@main.route('/matches')
@login_required
def matches():

    matches = Match.query.filter(
        (Match.user1_id == current_user.id) |
        (Match.user2_id == current_user.id)
    ).all()

    return render_template('matches.html', matches=matches)


# ================= CHAT =================

@main.route('/chat/<user_id>')
@login_required
def chat(user_id):

    other_user = User.query.get_or_404(user_id)

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    return render_template(
        'chat.html',
        messages=messages,
        other_user=other_user
    )


# ================= CONVERSATIONS =================

@main.route('/messages')
@login_required
def messages():
    return render_template('conversations.html')


# ================= UNREAD COUNT =================

@main.route('/messages/unread-count')
@login_required
def unread_count():
    count = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()

    return jsonify({"count": count})
