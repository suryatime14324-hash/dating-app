from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import os
import bleach

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
# AUTH
# =====================================================

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.discover'))

    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        age = request.form.get('age', type=int)
        gender = request.form.get('gender', '')
        looking_for = request.form.get('looking_for', 'everyone')

        if not all([email, password, name, age, gender]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('main.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('main.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('main.register'))

        if age < 18:
            flash('You must be 18+', 'error')
            return redirect(url_for('main.register'))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = Profile(
            user_id=user.id,
            name=name,
            age=age,
            gender=gender,
            looking_for=looking_for,
            interests=json.dumps([])
        )

        db.session.add(profile)
        db.session.commit()

        login_user(user)
        flash('Welcome! Complete your profile.', 'success')
        return redirect(url_for('main.edit_profile'))

    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.discover'))

    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            user.last_active = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for('main.discover'))

        flash('Invalid credentials', 'error')

    return render_template('login.html')


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
    if not current_user.profile:
        return redirect(url_for('main.edit_profile'))

    interests = []
    if current_user.profile.interests:
        try:
            interests = json.loads(current_user.profile.interests)
        except:
            interests = []

    return render_template(
        'profile.html',
        user=current_user,
        interests=interests
    )


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

        upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        for field in ['photo1', 'photo2', 'photo3']:
            if field in request.files:
                file = request.files[field]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.id}_{field}_{file.filename}")
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    setattr(profile, field, f'/static/uploads/{filename}')

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('main.profile'))

    interests = []
    if profile and profile.interests:
        try:
            interests = json.loads(profile.interests)
        except:
            interests = []

    return render_template('edit_profile.html', profile=profile, interests=interests)


# =====================================================
# DISCOVER
# =====================================================

@main.route('/discover')
@login_required
def discover():

    if not current_user.profile:
        return redirect(url_for('main.edit_profile'))

    profile = current_user.profile

    query = User.query.join(Profile).filter(
        User.id != current_user.id,
        User.is_active == True,
        Profile.age >= profile.min_age,
        Profile.age <= profile.max_age
    )

    if profile.looking_for != 'everyone':
        query = query.filter(Profile.gender == profile.looking_for)

    liked_ids = [l.liked_id for l in current_user.likes_given.all()]

    if liked_ids:
        query = query.filter(~User.id.in_(liked_ids))

    users = query.order_by(db.func.random()).limit(10).all()

    users_data = []

    for user in users:
        interests = []
        if user.profile and user.profile.interests:
            try:
                interests = json.loads(user.profile.interests)
            except:
                interests = []

        users_data.append({
            "user": user,
            "interests": interests
        })

    return render_template('discover.html', users=users_data)


# =====================================================
# LIKE / MATCH
# =====================================================

@main.route('/like/<user_id>', methods=['POST'])
@login_required
def like_user(user_id):

    if user_id == current_user.id:
        return jsonify({'error': 'Cannot like yourself'}), 400

    if Like.query.filter_by(liker_id=current_user.id, liked_id=user_id).first():
        return jsonify({'error': 'Already liked'}), 400

    like = Like(liker_id=current_user.id, liked_id=user_id)
    db.session.add(like)

    existing = Match.query.filter(
        ((Match.user1_id == current_user.id) & (Match.user2_id == user_id)) |
        ((Match.user1_id == user_id) & (Match.user2_id == current_user.id))
    ).first()

    is_new_match = False

    if not existing:
        existing = Match(user1_id=current_user.id, user2_id=user_id, user1_likes=True)
        db.session.add(existing)
    else:
        if existing.user1_id == current_user.id:
            existing.user1_likes = True
        else:
            existing.user2_likes = True

        if existing.user1_likes and existing.user2_likes:
            existing.is_match = True
            existing.matched_at = datetime.utcnow()
            is_new_match = True

    db.session.commit()

    return jsonify({
        "success": True,
        "is_match": is_new_match
    })


# =====================================================
# MATCHES
# =====================================================

@main.route('/matches')
@login_required
def matches():
    matches = current_user.get_matches()
    return render_template('matches.html', matches=matches)


# =====================================================
# MESSAGING
# =====================================================

@main.route('/messages/<user_id>')
@login_required
def chat(user_id):

    match = Match.query.filter(
        ((Match.user1_id == current_user.id) & (Match.user2_id == user_id)) |
        ((Match.user1_id == user_id) & (Match.user2_id == current_user.id)),
        Match.is_match == True
    ).first()

    if not match:
        flash('Not matched', 'error')
        return redirect(url_for('main.matches'))

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    return render_template('chat.html', messages=messages, other_user_id=user_id)
