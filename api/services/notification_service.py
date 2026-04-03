from typing import Optional, TYPE_CHECKING, List
from django.contrib.auth import get_user_model

from api.models import Notification, Post
from api.services.push_service import send_push_notification

# ✅ TYPE SAFE (Pylance friendly)
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    UserType = AbstractUser
else:
    UserType = get_user_model()


# ───────────────── CORE FUNCTION ─────────────────

def _create_notification(
    *,
    recipient: UserType,
    sender: UserType,
    notification_type: str,
    text: str = "",
    post: Optional[Post] = None,
    comment_id: Optional[int] = None,
    chat_room_id: Optional[str] = None,
    target_user: Optional[UserType] = None,
):
    """
    🔥 SINGLE SOURCE OF TRUTH

    - Creates DB notification
    - Sends push notification
    - Prevents self notification
    - Adds deep-link payload (VERY IMPORTANT)
    """

    if recipient == sender:
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        text=text,
        post=post,
        comment_id=comment_id,
        chat_room_id=chat_room_id,
        target_user=target_user,
    )

    # ───────────── BUILD DATA PAYLOAD ─────────────

    data_payload = {
        "type": notification_type,
        "notification_id": str(notification.id),
    }

    # attach optional data
    if post:
        data_payload["post_id"] = str(post.id)

    if chat_room_id:
        data_payload["chat_room_id"] = str(chat_room_id)

    if target_user:
        data_payload["user_id"] = str(target_user.id)

    if comment_id:
        data_payload["comment_id"] = str(comment_id)

    # ───────────── PUSH NOTIFICATION ─────────────

    try:
        send_push_notification(
            user=recipient,
            title="Amikiyo",
            body=text,
            data=data_payload,  # 🔥 THIS IS THE MAGIC
        )
    except Exception as e:
        print("🚨 Push error:", e)

    return notification


# ───────────────── LIKE ─────────────────

def notify_like(sender: UserType, post: Post):
    return _create_notification(
        recipient=post.author.user,
        sender=sender,
        notification_type="like",
        post=post,
        text=f"{sender.username} liked your post",
    )


# ───────────────── COMMENT ─────────────────

def notify_comment(sender: UserType, post: Post, comment_text: str):
    safe_text = (comment_text or "")[:50]

    return _create_notification(
        recipient=post.author.user,
        sender=sender,
        notification_type="comment",
        post=post,
        text=f"{sender.username} commented: {safe_text}",
    )


# ───────────────── REPLY ─────────────────

def notify_reply(sender: UserType, comment_user: UserType, comment_id: int):
    return _create_notification(
        recipient=comment_user,
        sender=sender,
        notification_type="reply",
        comment_id=comment_id,
        text=f"{sender.username} replied to your comment",
    )


# ───────────────── FOLLOW ─────────────────

def notify_follow(sender: UserType, target_user: UserType):
    return _create_notification(
        recipient=target_user,
        sender=sender,
        notification_type="follow",
        target_user=target_user,
        text=f"{sender.username} started following you",
    )


# ───────────────── NEW POST ─────────────────

def notify_new_post(
    sender: UserType,
    followers_queryset,
    post: Post
) -> List[Notification]:

    notifications = []

    for follower in followers_queryset:
        if follower.user == sender:
            continue

        notif = _create_notification(
            recipient=follower.user,
            sender=sender,
            notification_type="post",
            post=post,
            text=f"{sender.username} posted something new",
        )

        if notif:
            notifications.append(notif)

    return notifications


# ───────────────── NEW THOUGHT ─────────────────

def notify_new_thought(
    sender: UserType,
    followers_queryset,
    post: Post
) -> List[Notification]:

    notifications = []

    for follower in followers_queryset:
        if follower.user == sender:
            continue

        notif = _create_notification(
            recipient=follower.user,
            sender=sender,
            notification_type="thought",
            post=post,
            text=f"{sender.username} shared a thought",
        )

        if notif:
            notifications.append(notif)

    return notifications


# ───────────────── DM ─────────────────

def notify_dm(
    sender: UserType,
    receiver: UserType,
    chat_room_id: str,
    message: str
):
    safe_msg = (message or "")[:50]

    return _create_notification(
        recipient=receiver,
        sender=sender,
        notification_type="dm",
        chat_room_id=chat_room_id,
        text=f"{sender.username}: {safe_msg}",
    )