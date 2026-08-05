from datetime import datetime

from models import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship for product (optional)
    product = db.relationship("Product", backref="messages", lazy=True)

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message": self.message,
            "is_read": self.is_read,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "product_id": self.product_id,
        }

    def __repr__(self):
        return f"<Message {self.id}>"