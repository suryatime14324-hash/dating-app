from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
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

# ============================================
# HOME & AUTH
# ============================================

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.discover'))
    return render_template('index.html')

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
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('main.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('main.register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('main.register'))
        
        if age < 18:
            flash('You must be at least 18 years old', 'error')
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
            looking_for=looking_for
        )
        db.session.add(profile)
        db.session.commit()
        
        login_user(user)
        flash('Welcome! Complete your profile to start matching.', 'success')
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
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.discover'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

# ============================================
# PROFILE
# ============================================

@main.route('/profile')
@login_required
def profile():
    if not current_user.profile:
        return redirect(url_for('main.edit_profile'))
    return render_template('profile.html', user=current_user)

@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = current_user.profile
    
    if request.method == 'POST':
        if not profile:
            profile = Profile(user_id=current_user.id)
            db.session.add(profile)
        
        profile.name = request.form.get('name', profile.name if profile else '').strip()
        profile.age = request.form.get('age', type=int) or (profile.age if profile else 18)
        profile.gender = request.form.get('gender', profile.gender if profile else '')
        profile.looking_for = request.form.get('looking_for', profile.looking_for if profile else 'everyone')
        profile.bio = request.form.get('bio', '').strip()
        profile.occupation = request.form.get('occupation', '').strip()
        profile.city = request.form.get('city', '').strip()
        profile.min_age = request.form.get('min_age', type=int) or 18
        profile.max_age = request.form.get('max_age', type=int) or 99
        profile.max_distance = request.form.get('max_distance', type=int) or 100
        
        # Handle interests
        interests = request.form.getlist('interests')
        profile.interests = json.dumps(interests)
        
        # Handle photo uploads
        upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        for i, photo_field in enumerate(['photo1', 'photo2', 'photo3'], 1):
            if photo_field in request.files:
                file = request.files[photo_field]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.id}_{i}_{file.filename}")
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    setattr(profile, photo_field, f'/static/uploads/{filename}')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    interests = json.loads(profile.interests) if profile and profile.interests else []
    return render_template('edit_profile.html', profile=profile, interests=interests)

@main.route('/user/<user_id>')
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Check if already matched
    existing_match = Match.query.filter(
        ((Match.user1_id == current_user.id) & (Match.user2_id == user_id)) |
        ((Match.user1_id == user_id) & (Match.user2_id == current_user.id))
    ).first()
    
    is_match = existing_match.is_match if existing_match else False
    has_liked = Like.query.filter_by(liker_id=current_user.id, liked_id=user_id).first() is not None
    
    return render_template('view_user.html', user=user, is_match=is_match, has_liked=has_liked)

# ============================================
# DISCOVER & MATCHING
# ============================================

@main.route('/discover')
@login_required
def discover():
    if not current_user.profile:
        flash('Please complete your profile first', 'info')
        return redirect(url_for('main.edit_profile'))
    
    profile = current_user.profile
    
    # Build query for potential matches
    query = User.query.join(Profile).filter(
        User.id != current_user.id,
        User.is_active == True,
        Profile.age >= profile.min_age,
        Profile.age <= profile.max_age
    )
    
    # Gender filter
    if profile.looking_for != 'everyone':
        query = query.filter(Profile.gender == profile.looking_for)
    
    # Filter by who wants to see current user's gender
    if profile.gender == 'male':
        query = query.filter(Profile.looking_for.in_(['male', 'everyone']))
    elif profile.gender == 'female':
        query = query.filter(Profile.looking_for.in_(['female', 'everyone']))
    
    # Exclude already liked/matched users
    liked_ids = [l.liked_id for l in current_user.likes_given.all()]
    matched_users = []
    for match in current_user.get_matches():
        matched_users.append(match.user1_id if match.user2_id == current_user.id else match.user2_id)
    
    exclude_ids = liked_ids + matched_users
    if exclude_ids:
        query = query.filter(~User.id.in_(exclude_ids))
    
    # Get random profiles
    users = query.order_by(db.func.random()).limit(10).all()
    
    return render_template('discover.html', users=users)

@main.route('/like/<user_id>', methods=['POST'])
@login_required
def like_user(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot like yourself'}), 400
    
    # Check if already liked
    existing_like = Like.query.filter_by(liker_id=current_user.id, liked_id=user_id).first()
    if existing_like:
        return jsonify({'error': 'Already liked'}), 400
    
    # Create like
    like = Like(liker_id=current_user.id, liked_id=user_id)
    db.session.add(like)
    
    # Check for match
    match = Match.query.filter(
        ((Match.user1_id == current_user.id) & (Match.user2_id == user_id)) |
        ((Match.user1_id == user_id) & (Match.user2_id == current_user.id))
    ).first()
    
    is_new_match = False
    
    if not match:
        # Create new match record
        match = Match(user1_id=current_user.id, user2_id=user_id, user1_likes=True)
        db.session.add(match)
    else:
        # Update existing match
        if match.user1_id == current_user.id:
            match.user1_likes = True
        else:
            match.user2_likes = True
        
        is_new_match = match.check_match()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_match': is_new_match,
        'message': 'It\'s a match!' if is_new_match else 'Liked!'
    })

@main.route('/pass/<user_id>', methods=['POST'])
@login_required
def pass_user(user_id):
    # Simply record that user passed (optional, for ML)
    return jsonify({'success': True})

@main.route('/matches')
@login_required
def matches():
    matches = current_user.get_matches()
    return render_template('matches.html', matches=matches)

# ============================================
# MESSAGING
# ============================================

@main.route('/messages')
@login_required
def messages():
    conversations = current_user.get_conversations()
    return render_template('conversations.html', conversations=conversations)

@main.route('/messages/<user_id>')
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Verify they are matched
    match = Match.query.filter(
        ((Match.user1_id == current_user.id) & (Match.user2_id == user_id)) |
        ((Match.user1_id == user_id) & (Match.user2_id == current_user.id)),
        Match.is_match == True
    ).first()
    
    if not match:
        flash('You can only message matched users', 'error')
        return redirect(url_for('main.matches'))
    
    # Get messages
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    # Mark messages as read
    unread = Message.query.filter_by(sender_id=user_id, receiver_id=current_user.id, is_read=False).all()
    for msg in unread:
        msg.is_read = True
        msg.read_at = datetime.utcnow()
    db.session.commit()
    
    return render_template('chat.html', other_user=other_user, messages=messages)

@main.route('/messages/<user_id>/send', methods=['POST'])
@login_required
def send_message(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Verify they are matched
    match = Match.query.filter(
        ((Match.user1_id == current_user.id) & (Match.user2_id == user_id)) |
        ((Match.user1_id == user_id) & (Match.user2_id == current_user.id)),
        Match.is_match == True
    ).first()
    
    if not match:
        return jsonify({'error': 'Not matched'}), 403
    
    content = request.json.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    if len(content) > 1000:
        return jsonify({'error': 'Message too long'}), 400
    
    # Sanitize content
    content = bleach.clean(content, tags=[], strip=True)
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=user_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify(message.to_dict())

@main.route('/messages/unread-count')
@login_required
def unread_count():
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

# ============================================
# API ENDPOINTS
# ============================================

@main.route('/api/profile/<user_id>')
@login_required
def api_profile(user_id):
    user = User.query.get_or_404(user_id)
    profile = user.profile
    
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify({
        'id': user.id,
        'name': profile.name,
        'age': profile.age,
        'gender': profile.gender,
        'bio': profile.bio,
        'occupation': profile.occupation,
        'city': profile.city,
        'photo1': profile.photo1,
        'photo2': profile.photo2,
        'photo3': profile.photo3,
        'interests': json.loads(profile.interests) if profile.interests else []
    })
