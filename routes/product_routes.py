from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import os
import uuid

from models import db
from models.cart import CartItem
from models.message import Message
from models.order import Order, OrderItem, OrderDelivery
from models.product import Product

product_bp = Blueprint("products", __name__)
INDIA_STATES_AND_UT = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
    "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
]

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def is_allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None

    if not is_allowed_image(file_storage.filename):
        return None, "Allowed image types: png, jpg, jpeg, webp, gif."

    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[1].lower()
    generated = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(product_bp.root_path, "..", "static", "uploads", generated)
    upload_path = os.path.abspath(upload_path)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file_storage.save(upload_path)
    return f"uploads/{generated}", None


@product_bp.route("/")
def home():
    """Home page with search and filters"""
    page = request.args.get("page", 1, type=int)
    per_page = 12

    query = Product.query.filter_by(status="available").order_by(Product.created_at.desc())

    # Search filters
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    location = request.args.get("location", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    if keyword:
        query = query.filter(
            or_(
                Product.title.ilike(f"%{keyword}%"),
                Product.description.ilike(f"%{keyword}%")
            )
        )
    if category:
        query = query.filter(Product.category == category)
    if location:
        query = query.filter(Product.location.ilike(f"%{location}%"))
    if min_price:
        try:
            query = query.filter(Product.price >= float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            query = query.filter(Product.price <= float(max_price))
        except ValueError:
            pass

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    # Get all categories for filter dropdown
    categories = Product.CATEGORIES

    return render_template(
        "home.html",
        products=products,
        pagination=pagination,
        categories=categories,
        india_states=INDIA_STATES_AND_UT,
        filters={
            "keyword": keyword,
            "category": category,
            "location": location,
            "min_price": min_price,
            "max_price": max_price,
        }
    )


@product_bp.route("/products/new", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        location = f"{city}, {state}" if city and state else (state or city)
        image_file = request.files.get("image")

        # Validation
        errors = []
        if not title:
            errors.append("Title is required.")
        if not price:
            errors.append("Price is required.")
        else:
            try:
                price = float(price)
                if price < 0:
                    errors.append("Price cannot be negative.")
            except ValueError:
                errors.append("Invalid price.")
        if not description:
            errors.append("Description is required.")
        if len(description) < 20:
            errors.append("Description should be at least 20 characters.")
        if not category:
            errors.append("Category is required.")
        if not location:
            errors.append("Location is required.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("product_form.html", categories=Product.CATEGORIES, india_states=INDIA_STATES_AND_UT)

        image_path, image_error = save_uploaded_image(image_file)
        if image_error:
            flash(image_error, "danger")
            return render_template("product_form.html", categories=Product.CATEGORIES, india_states=INDIA_STATES_AND_UT)

        product = Product(
            user_id=current_user.id,
            title=title,
            price=price,
            description=description,
            category=category,
            location=location,
            image=image_path,
        )
        db.session.add(product)
        db.session.commit()

        flash("✅ Product listed successfully!", "success")
        return redirect(url_for("products.product_detail", product_id=product.id))

    return render_template("product_form.html", categories=Product.CATEGORIES, india_states=INDIA_STATES_AND_UT)


@product_bp.route("/products/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    product.increment_views()

    # Get similar products (same category)
    similar_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id,
        Product.status == "available"
    ).limit(4).all()

    return render_template("product_detail.html", product=product, similar_products=similar_products)


@product_bp.route("/cart")
@login_required
def cart():
    items = (
        CartItem.query.filter_by(user_id=current_user.id)
        .order_by(CartItem.created_at.desc())
        .all()
    )
    subtotal = sum((item.product.price * item.quantity) for item in items if item.product)
    return render_template("cart.html", cart_items=items, subtotal=subtotal)


def get_checkout_summary(user_id):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    valid_items = [item for item in cart_items if item.product and item.product.status == "available"]
    subtotal = sum((item.product.price * item.quantity) for item in valid_items)
    return cart_items, valid_items, subtotal


@product_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if product.user_id == current_user.id:
        flash("You cannot add your own product to cart.", "warning")
        return redirect(url_for("products.product_detail", product_id=product_id))
    if product.status != "available":
        flash("This product is not available.", "warning")
        return redirect(url_for("products.product_detail", product_id=product_id))

    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash("Product already exists in your cart.", "info")
    else:
        db.session.add(CartItem(user_id=current_user.id, product_id=product_id, quantity=1))
        db.session.commit()
        flash("Product added to cart.", "success")
    return redirect(url_for("products.cart"))


@product_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_cart_item(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("products.cart"))


@product_bp.route("/checkout", methods=["GET"])
@login_required
def checkout():
    cart_items, valid_items, subtotal = get_checkout_summary(current_user.id)
    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products.cart"))
    if not valid_items:
        flash("No available products to checkout.", "warning")
        return redirect(url_for("products.cart"))

    return render_template("checkout.html", items=valid_items, subtotal=subtotal, india_states=INDIA_STATES_AND_UT)


@product_bp.route("/checkout/place", methods=["POST"])
@login_required
def place_order():
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    address_line = request.form.get("address_line", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    pincode = request.form.get("pincode", "").strip()
    payment_method = request.form.get("payment_method", "cod").strip()

    if not all([full_name, phone, address_line, city, state, pincode]):
        flash("Please fill delivery address details.", "danger")
        _, valid_items, subtotal = get_checkout_summary(current_user.id)
        return render_template("checkout.html", items=valid_items, subtotal=subtotal, india_states=INDIA_STATES_AND_UT)
    if payment_method != "cod":
        flash("Currently only Cash on Delivery is available.", "warning")
        payment_method = "cod"

    cart_items, valid_items, _ = get_checkout_summary(current_user.id)
    if not cart_items or not valid_items:
        flash("No available products to checkout.", "warning")
        return redirect(url_for("products.cart"))

    order = Order(buyer_id=current_user.id, total_amount=0.0, status="placed")
    db.session.add(order)
    db.session.flush()

    total = 0.0
    for cart_item in valid_items:
        product = cart_item.product
        item_total = product.price * cart_item.quantity
        total += item_total

        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                seller_id=product.user_id,
                quantity=cart_item.quantity,
                unit_price=product.price,
                title_snapshot=product.title,
            )
        )
        product.status = "sold"
        # Seller notification via system message.
        db.session.add(
            Message(
                sender_id=current_user.id,
                receiver_id=product.user_id,
                product_id=product.id,
                message=f"Order Alert: Your item '{product.title}' has been sold.",
                is_read=False,
            )
        )

    order.total_amount = total
    db.session.add(
        OrderDelivery(
            order_id=order.id,
            full_name=full_name,
            phone=phone,
            address_line=address_line,
            city=city,
            state=state,
            pincode=pincode,
            payment_method=payment_method,
        )
    )
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Order placed successfully. Seller has been notified.", "success")
    return redirect(url_for("products.my_orders"))


@product_bp.route("/orders")
@login_required
def my_orders():
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)


@product_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.user_id != current_user.id:
        flash("You can only edit your own listings.", "danger")
        return redirect(url_for("products.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        location = f"{city}, {state}" if city and state else (state or city)
        image_file = request.files.get("image")
        status = request.form.get("status", "available")

        # Validation
        if not title or not price or not description or not category or not location:
            flash("Please fill all required fields.", "danger")
            return render_template("product_form.html", product=product, categories=Product.CATEGORIES, india_states=INDIA_STATES_AND_UT)

        try:
            price = float(price)
        except ValueError:
            flash("Invalid price.", "danger")
            return render_template("product_form.html", product=product, categories=Product.CATEGORIES, india_states=INDIA_STATES_AND_UT)

        product.title = title
        product.price = price
        product.description = description
        product.category = category
        product.location = location
        product.status = status

        if image_file and image_file.filename:
            image_path, image_error = save_uploaded_image(image_file)
            if image_error:
                flash(image_error, "danger")
                return render_template("product_form.html", product=product, categories=Product.CATEGORIES, india_states=INDIA_STATES_AND_UT, is_edit=True)
            product.image = image_path

        db.session.commit()
        flash("✅ Product updated successfully!", "success")
        return redirect(url_for("products.product_detail", product_id=product.id))

    return render_template("product_form.html", product=product, categories=Product.CATEGORIES, india_states=INDIA_STATES_AND_UT, is_edit=True)


@product_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.user_id != current_user.id:
        flash("You can only delete your own listings.", "danger")
        return redirect(url_for("products.dashboard"))

    db.session.delete(product)
    db.session.commit()
    flash("🗑️ Listing deleted successfully.", "info")
    return redirect(url_for("products.dashboard"))


@product_bp.route("/dashboard")
@login_required
def dashboard():
    my_products = Product.query.filter_by(user_id=current_user.id).order_by(Product.created_at.desc()).all()

    # Stats
    total_listings = len(my_products)
    available_listings = len([p for p in my_products if p.status == "available"])
    sold_listings = len([p for p in my_products if p.status == "sold"])
    total_views = sum(p.views for p in my_products)

    return render_template(
        "dashboard.html",
        my_products=my_products,
        stats={
            "total": total_listings,
            "available": available_listings,
            "sold": sold_listings,
            "views": total_views,
        }
    )


@product_bp.route("/about")
def about():
    return render_template("about.html")


@product_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please fill all fields before submitting.", "danger")
        else:
            flash("Thanks for contacting us. We will get back to you soon.", "success")
            return redirect(url_for("products.contact"))
    return render_template("contact.html")