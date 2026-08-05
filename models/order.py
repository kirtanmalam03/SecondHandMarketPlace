from datetime import datetime

from models import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default="placed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    buyer = db.relationship("User", backref=db.backref("orders", lazy=True))


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    title_snapshot = db.Column(db.String(140), nullable=False)

    order = db.relationship("Order", backref=db.backref("items", lazy=True, cascade="all, delete-orphan"))
    product = db.relationship("Product", backref=db.backref("order_items", lazy=True))


class OrderDelivery(db.Model):
    __tablename__ = "order_deliveries"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True, unique=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False, default="cod")

    order = db.relationship("Order", backref=db.backref("delivery", uselist=False, lazy=True, cascade="all, delete-orphan"))
