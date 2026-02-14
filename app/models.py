from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Profile relationship
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    # Messages
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    
    # Matches
    matches_as_user1 = db.relationship('Match', foreign_keys='Match.user1_id', backref='user1', lazy='dynamic')
    matches_as_user2 = db.relationship('Match', foreign_keys='Match.user2_id', backref='user2', lazy='dynamic')
    
    # Likes
    likes_given = db.relationship('Like', foreign_keys='Like.liker_id', backref='liker', lazy='dynamic')
    likes_received = db.relationship('Like', foreign_keys='Like.liked_id', backref='liked', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_matches(self):
        """Get all matches for this user"""
        from_match = Match.query.filter_by(user1_id=self.id, is_match=True).all()
        to_match = Match.query.filter_by(user2_id=self.id, is_match=True).all()
        return from_match + to_match
    
    def get_conversations(self):
        """Get all users this user has messaged or received messages from"""
        sent = db.session.query(Message.receiver_id).filter_by(sender_id=self.id).distinct()
        received = db.session.query(Message.sender_id).filter_by(receiver_id=self.id).distinct()
        user_ids = [u[0] for u in sent.union(received).all()]
        return User.query.filter(User.id.in_(user_ids)).all() if user_ids else []


class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Basic info
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    looking_for = db.Column(db.String(20), default='everyone')  # male, female, everyone
    
    # Location
    city = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # About
    bio = db.Column(db.Text)
    occupation = db.Column(db.String(100))
    
    # Photos
    photo1 = db.Column(db.String(500))
    photo2 = db.Column(db.String(500))
    photo3 = db.Column(db.String(500))
    
    # Preferences
    min_age = db.Column(db.Integer, default=18)
    max_age = db.Column(db.Integer, default=99)
    max_distance = db.Column(db.Integer, default=100)  # km
    
    # Interests (stored as JSON string)
    interests = db.Column(db.Text, default='[]')
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Like(db.Model):
    __tablename__ = 'likes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    liker_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    liked_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('liker_id', 'liked_id', name='unique_like'),)


class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user1_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    user1_likes = db.Column(db.Boolean, default=False)
    user2_likes = db.Column(db.Boolean, default=False)
    is_match = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    matched_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user1_id', 'user2_id', name='unique_match_pair'),)
    
    def check_match(self):
        """Check if both users like each other"""
        if self.user1_likes and self.user2_likes:
            self.is_match = True
            self.matched_at = datetime.utcnow()
            return True
        return False
    
    def get_other_user(self, current_user_id):
        """Get the other user in the match"""
        return self.user2 if self.user1_id == current_user_id else self.user1


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read
        }
