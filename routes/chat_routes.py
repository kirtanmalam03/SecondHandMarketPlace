from flask import Blueprint, render_template, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

from models import db
from models.message import Message
from models.user import User
from models.product import Product

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def get_room_name(user_a_id, user_b_id):
    """Generate unique room name for two users"""
    first, second = sorted([user_a_id, user_b_id])
    return f"room_{first}_{second}"


@chat_bp.route("/")
@login_required
def inbox():
    """Show all conversations for current user"""
    conversations = {}
    all_messages = (
        Message.query.filter((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id))
        .order_by(Message.timestamp.desc())
        .all()
    )

    for msg in all_messages:
        other_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        if other_id not in conversations:
            other_user = User.query.get(other_id)
            if not other_user:
                continue
            conversations[other_id] = {
                "user": other_user,
                "last_message": msg.message,
                "last_time": msg.timestamp,
                "unread": 0,
            }
        if msg.receiver_id == current_user.id and not msg.is_read:
            conversations[other_id]["unread"] += 1

    sorted_conversations = sorted(conversations.values(), key=lambda x: x["last_time"], reverse=True)

    return render_template("inbox.html", conversations=sorted_conversations)


@chat_bp.route("/user/<int:user_id>")
@login_required
def chat_with_user(user_id):
    """Chat with a specific user"""
    other_user = User.query.get_or_404(user_id)

    if other_user.id == current_user.id:
        return render_template("chat.html", other_user=None, messages=[], room="", error="You cannot chat with yourself.")

    # Mark unread messages as read in one query.
    Message.query.filter_by(sender_id=user_id, receiver_id=current_user.id, is_read=False).update(
        {"is_read": True}, synchronize_session=False
    )
    db.session.commit()

    # Fetch messages after status update
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    room = get_room_name(current_user.id, user_id)

    return render_template("chat.html", other_user=other_user, messages=messages, room=room)


@chat_bp.route("/product/<int:product_id>")
@login_required
def chat_about_product(product_id):
    """Start chat about a specific product"""
    product = Product.query.get_or_404(product_id)

    if product.user_id == current_user.id:
        flash("You cannot chat with yourself about your own product.", "warning")
        return redirect(url_for("products.product_detail", product_id=product_id))

    return redirect(url_for("chat.chat_with_user", user_id=product.user_id))


@chat_bp.route("/api/unread-count")
@login_required
def unread_count():
    """API endpoint for unread message count"""
    count = current_user.get_unread_count()
    return jsonify({"unread": count})


@chat_bp.route("/delete/<int:message_id>", methods=["POST"])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.sender_id != current_user.id:
        flash("You can only delete your own messages.", "danger")
        return redirect(url_for("chat.inbox"))

    redirect_user_id = message.receiver_id
    db.session.delete(message)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("chat.chat_with_user", user_id=redirect_user_id))