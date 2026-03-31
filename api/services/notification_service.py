from typing import Optional
from django.contrib.auth import get_user_model
from api.models import Notification, Post
from typing import Optional, TYPE_CHECKING

from django.contrib.auth import get_user_model
from api.models import Notification, Post

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User
else:
    User = get_user_model()




# ───────────────── CORE FUNCTION ─────────────────

def _create_notification(
    *,
    recipient: User,
    sender: User,
    notification_type: str,
    text: str = "",
    post: Optional[Post] = None,
    comment_id: Optional[int] = None,
    chat_room_id: Optional[str] = None,
    target_user: Optional[User] = None,
):
    """
    Central notification creator.
    Prevents self-notifications.
    """

    if recipient == sender:
        return None

    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        text=text,
        post=post,
        comment_id=comment_id,
        chat_room_id=chat_room_id,
        target_user=target_user,
    )


# ───────────────── LIKE ─────────────────

def notify_like(sender: User, post: Post):
    recipient = post.author.user

    return _create_notification(
        recipient=recipient,
        sender=sender,
        notification_type="like",
        post=post,
        text=f"{sender.username} liked your post",
    )


# ───────────────── COMMENT ─────────────────

def notify_comment(sender: User, post: Post, text: str = ""):
    recipient = post.author.user

    return _create_notification(
        recipient=recipient,
        sender=sender,
        notification_type="comment",
        post=post,
        text=f"{sender.username} commented: {text[:50]}",
    )


# ───────────────── REPLY ─────────────────

def notify_reply(sender: User, comment_user: User, comment_id: int):
    return _create_notification(
        recipient=comment_user,
        sender=sender,
        notification_type="reply",
        comment_id=comment_id,
        text=f"{sender.username} replied to your comment",
    )


# ───────────────── FOLLOW ─────────────────

def notify_follow(sender: User, target_user: User):
    return _create_notification(
        recipient=target_user,
        sender=sender,
        notification_type="follow",
        target_user=target_user,
        text=f"{sender.username} started following you",
    )


# ───────────────── NEW POST ─────────────────

def notify_new_post(sender: User, followers_queryset, post: Post):
    """
    Notify followers about new post
    """

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

def notify_new_thought(sender: User, followers_queryset, post: Post):
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

def notify_dm(sender: User, receiver: User, chat_room_id, message: str):
    return _create_notification(
        recipient=receiver,
        sender=sender,
        notification_type="dm",
        chat_room_id=chat_room_id,
        text=f"{sender.username}: {message[:50]}",
    )