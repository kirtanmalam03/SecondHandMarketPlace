import os
from app import create_app, db
from models.user import User
from models.product import Product

def seed_database():
    app = create_app()
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        # Seed sample users if empty or not existing
        seller = User.query.filter_by(email="seller@example.com").first()
        if not seller:
            seller = User(
                name="Rahul Sharma",
                email="seller@example.com",
                location="Delhi",
                phone="+91 9876543210"
            )
            seller.set_password("seller123")
            db.session.add(seller)

        buyer = User.query.filter_by(email="buyer@example.com").first()
        if not buyer:
            buyer = User(
                name="Priya Patel",
                email="buyer@example.com",
                location="Maharashtra",
                phone="+91 9123456789"
            )
            buyer.set_password("buyer123")
            db.session.add(buyer)

        db.session.commit()

        # Check existing products
        if Product.query.count() < 4:
            sample_products = [
                {
                    "title": "Apple iPhone 14 Pro Max 256GB - Deep Purple",
                    "price": 72500.0,
                    "category": "Electronics",
                    "location": "Mumbai, Maharashtra",
                    "description": "Like new condition. 92% battery health. Comes with original box, cable, and protective case. No scratches or dents.",
                    "image": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
                    "status": "available",
                    "views": 48
                },
                {
                    "title": "MacBook Air M2 13.6-inch 8GB/512GB Midnight",
                    "price": 84000.0,
                    "category": "Electronics",
                    "location": "Bengaluru, Karnataka",
                    "description": "Used for 6 months for light office work. Excellent battery backup. Original charger included. Under Apple warranty.",
                    "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
                    "status": "available",
                    "views": 112
                },
                {
                    "title": "Royal Enfield Classic 350 Stealth Black",
                    "price": 165000.0,
                    "category": "Vehicles",
                    "location": "Pune, Maharashtra",
                    "description": "2022 Model, single owner, 12,000 km driven. All service records available at RE service center. Insurance valid till 2027.",
                    "image": "https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=600&auto=format&fit=crop&q=80",
                    "status": "available",
                    "views": 85
                },
                {
                    "title": "Modern Ergonomic Office Chair with Mesh Back",
                    "price": 4500.0,
                    "category": "Furniture",
                    "location": "Delhi, Delhi",
                    "description": "High back mesh chair with adjustable headrest and lumbar support. 1 year old, very clean and comfortable.",
                    "image": "https://images.unsplash.com/photo-1580481072645-022f9a6d83d0?w=600&auto=format&fit=crop&q=80",
                    "status": "available",
                    "views": 34
                },
                {
                    "title": "Sony WH-1000XM4 Wireless Noise Canceling Headphones",
                    "price": 14999.0,
                    "category": "Electronics",
                    "location": "Hyderabad, Telangana",
                    "description": "Industry leading noise cancellation. Midnight Black color. Includes original carrying case, 3.5mm cable, and charging cable.",
                    "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
                    "status": "available",
                    "views": 62
                },
                {
                    "title": "Solid Teak Wood Dining Table with 4 Chairs",
                    "price": 18500.0,
                    "category": "Furniture",
                    "location": "Jaipur, Rajasthan",
                    "description": "Handcrafted pure teak wood dining set. Sturdy, beautiful natural wood grain finish. Moving out sale.",
                    "image": "https://images.unsplash.com/photo-1615066390971-03e4e1c36ddf?w=600&auto=format&fit=crop&q=80",
                    "status": "available",
                    "views": 29
                }
            ]

            for pdata in sample_products:
                prod = Product(
                    user_id=seller.id,
                    title=pdata["title"],
                    price=pdata["price"],
                    category=pdata["category"],
                    location=pdata["location"],
                    description=pdata["description"],
                    image=pdata["image"],
                    status=pdata["status"],
                    views=pdata["views"]
                )
                db.session.add(prod)

            db.session.commit()
            print("Successfully seeded marketplace with sample products and users!")
        else:
            print("Database already contains product listings.")

if __name__ == "__main__":
    seed_database()
