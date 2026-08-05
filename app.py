import os
from flask import Flask
from flask_socketio import SocketIO, join_room, emit
from flask_login import current_user

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Load environment variables when python-dotenv is installed.
if load_dotenv:
    load_dotenv()

from models import db, login_manager
from models.cart import CartItem
from models.message import Message
from models.order import Order, OrderItem
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.chat_routes import chat_bp

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")


def create_app():
    """Application factory pattern"""
    app = Flask(__name__, template_folder="static/templates")

    # Configuration
    db_dir = os.path.join(app.root_path, "database")
    os.makedirs(db_dir, exist_ok=True)
    default_db_path = os.path.join(db_dir, "marketplace.db").replace("\\", "/")
    default_db_uri = f"sqlite:///{default_db_path}"

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", default_db_uri)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    # Avoid non-portable pool options on SQLite.
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": 10,
            "pool_recycle": 3600,
        }

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(chat_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()


@app.context_processor
def inject_global_counts():
    try:
        if current_user and current_user.is_authenticated:
            cart_cnt = CartItem.query.filter_by(user_id=current_user.id).count()
            unread_cnt = current_user.get_unread_count()
            return {
                "cart_count": cart_cnt if cart_cnt is not None else 0,
                "unread_count": unread_cnt if unread_cnt is not None else 0,
            }
    except Exception:
        pass
    return {"cart_count": 0, "unread_count": 0}


def get_room_name(user_a_id, user_b_id):
    """Generate unique room name"""
    first, second = sorted([user_a_id, user_b_id])
    return f"room_{first}_{second}"


@socketio.on("join_room")
def handle_join_room(data):
    """Handle user joining a chat room"""
    room = data.get("room")
    if room:
        join_room(room)


@socketio.on("connect")
def handle_connect():
    """Join a personal room for notifications after socket connect."""
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")


@socketio.on("send_message")
def handle_send_message(data):
    """Handle sending a real-time message"""
    if not current_user.is_authenticated:
        emit("error", {"message": "You must be logged in to send messages."})
        return

    receiver_id = data.get("receiver_id")
    room = data.get("room")
    message_text = data.get("message", "").strip()
    product_id = data.get("product_id")

    if not receiver_id or not room or not message_text:
        emit("error", {"message": "Invalid message data."})
        return

    try:
        receiver_id = int(receiver_id)
    except (TypeError, ValueError):
        emit("error", {"message": "Invalid receiver id."})
        return

    # Save message to database
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message_text,
        product_id=int(product_id) if product_id else None,
    )
    db.session.add(message)
    db.session.commit()

    # Emit message to room
    emit("receive_message", {
        "message_id": message.id,
        "sender_id": current_user.id,
        "sender_name": current_user.name,
        "message": message_text,
        "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M"),
        "product_id": product_id,
    }, room=room)

    # Also emit notification to receiver if they're not in room
    emit("new_message_notification", {
        "from_user_id": current_user.id,
        "from_user_name": current_user.name,
        "message_preview": message_text[:50],
    }, room=f"user_{receiver_id}")


@socketio.on("typing")
def handle_typing(data):
    """Handle typing indicator"""
    if not current_user.is_authenticated:
        return

    room = data.get("room")
    is_typing = data.get("is_typing", False)

    emit("user_typing", {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "is_typing": is_typing,
    }, room=room, include_self=False)


@socketio.on("stop_typing")
def handle_stop_typing(data):
    """Handle stop typing indicator."""
    if not current_user.is_authenticated:
        return

    room = data.get("room")
    emit("stop_typing", {
        "user_id": current_user.id,
        "user_name": current_user.name,
    }, room=room, include_self=False)


@socketio.on("mark_read")
def handle_mark_read(data):
    """Mark messages as read"""
    if not current_user.is_authenticated:
        return

    message_ids = data.get("message_ids", [])
    if message_ids:
        Message.query.filter(Message.id.in_(message_ids), Message.receiver_id == current_user.id).update(
            {"is_read": True}, synchronize_session=False
        )
        db.session.commit()


if __name__ == "__main__":
    # Create database directory if not exists
    os.makedirs("database", exist_ok=True)

    socketio.run(app, debug=True, host="0.0.0.0", port=5000)