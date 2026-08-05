from datetime import datetime

from models import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="available")  # available, sold, reserved
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Categories list
    CATEGORIES = [
        "Electronics",
        "Mobiles",
        "Laptops",
        "Furniture",
        "Clothing",
        "Books",
        "Sports",
        "Toys",
        "Vehicles",
        "Pets",
        "Home Appliances",
        "Other"
    ]

    def increment_views(self):
        self.views += 1
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "description": self.description,
            "category": self.category,
            "image": self.image,
            "location": self.location,
            "status": self.status,
            "views": self.views,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "owner_name": self.owner.name if self.owner else None,
            "owner_id": self.user_id,
        }

    def __repr__(self):
        return f"<Product {self.title}>"