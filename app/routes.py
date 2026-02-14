from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import os

from app import db
from app.models import User, Profile, Like, Match, Message

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# =====================================================
# HOME
# =====================================================

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.discover'))
    return render_template('index.html')


# =====================================================
# AUTH (🔥 YOU WERE MISSING THIS)
# =====================================================

@main.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")


@main.route('/register', methods=['GET', 'POST'])
def register():
    return render_template("register.html")


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# =====================================================
# PROFILE
# =====================================================

@main.route('/profile')
@login_required
def profile():
    interests = []
    if current_user.profile and current_user.profile.interests:
        try:
            interests = json.loads(current_user.profile.interests)
        except:
            interests = []

    return render_template('profile.html', user=current_user, interests=interests)


@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = current_user.profile

    if request.method == 'POST':

        if not profile:
            profile = Profile(user_id=current_user.id)
            db.session.add(profile)

        profile.name = request.form.get('name', '').strip()
        profile.age = request.form.get('age', type=int)
        profile.gender = request.form.get('gender')
        profile.looking_for = request.form.get('looking_for')
        profile.bio = request.form.get('bio', '').strip()
        profile.occupation = request.form.get('occupation', '').strip()
        profile.city = request.form.get('city', '').strip()
        profile.min_age = request.form.get('min_age', type=int) or 18
        profile.max_age = request.form.get('max_age', type=int) or 99
        profile.max_distance = request.form.get('max_distance', type=int) or 100

        interests = request.form.getlist('interests')
        profile.interests = json.dumps(interests)

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        for field in ['photo1', 'photo2', 'photo3']:
            file = request.files.get(field)
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{field}_{file.filename}")
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                setattr(profile, field, f'/static/uploads/{filename}')

        db.session.commit()
        return redirect(url_for('main.profile'))

    return render_template('edit_profile.html', profile=profile)


# =====================================================
# VIEW USER
# =====================================================

@main.route('/user/<user_id>')
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)

    interests = []
    if user.profile and user.profile.interests:
        try:
            interests = json.loads(user.profile.interests)
        except:
            interests = []

    is_match = Match.query.filter(
        ((Match.user1_id == current_user.id) & (Match.user2_id == user_id)) |
        ((Match.user1_id == user_id) & (Match.user2_id == current_user.id)),
        Match.is_match == True
    ).first() is not None

    has_liked = Like.query.filter_by(
        liker_id=current_user.id,
        liked_id=user_id
    ).first() is not None

    return render_template(
        'view_user.html',
        user=user,
        interests=interests,
        is_match=is_match,
        has_liked=has_liked
    )


# =====================================================
# DISCOVER
# =====================================================

@main.route('/discover')
@login_required
def discover():
    profile = current_user.profile
    if not profile:
        return redirect(url_for('main.edit_profile'))

    users = User.query.join(Profile).filter(
        User.id != current_user.id
    ).order_by(db.func.random()).limit(10).all()

    return render_template('discover.html', users=users)


# =====================================================
# LIKE
# =====================================================

@main.route('/like/<user_id>', methods=['POST'])
@login_required
def like_user(user_id):

    if user_id == current_user.id:
        return jsonify({'error': 'Cannot like yourself'}), 400

    if Like.query.filter_by(liker_id=current_user.id, liked_id=user_id).first():
        return jsonify({'error': 'Already liked'}), 400

    db.session.add(Like(liker_id=current_user.id, liked_id=user_id))
    db.session.commit()

    return jsonify({"success": True, "is_match": False})


# =====================================================
# MATCHES (🔥 YOU WERE MISSING THIS)
# =====================================================

@main.route('/matches')
@login_required
def matches():
    return render_template('matches.html')


# =====================================================
# MESSAGES (🔥 YOU WERE MISSING THIS)
# =====================================================

@main.route('/messages')
@login_required
def messages():
    return render_template('conversations.html')
