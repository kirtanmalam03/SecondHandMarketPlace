from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from models import db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships
    products = db.relationship("Product", backref="owner", lazy=True, cascade="all, delete-orphan")
    sent_messages = db.relationship("Message", foreign_keys="Message.sender_id", backref="sender", lazy=True)
    received_messages = db.relationship("Message", foreign_keys="Message.receiver_id", backref="receiver", lazy=True)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def get_unread_count(self):
        """Get number of unread messages"""
        from models.message import Message
        return Message.query.filter_by(receiver_id=self.id, is_read=False).count()

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))