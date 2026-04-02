from django.db import models
from django.contrib.auth.models import AbstractUser

from django.conf import settings
from django.db.models.functions import Lower
from django.db.models import Q

import uuid

class User(AbstractUser):
    firebase_uid = models.CharField(max_length=128, unique=True, null=True)

    def __str__(self):
        return self.username



from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Story(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories"
    )

    image = models.ImageField(upload_to="stories/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_active(self):
        return self.created_at >= timezone.now() - timedelta(hours=24)

    def __str__(self):
        return f"{self.user.username} story"
    

class StoryView(models.Model):
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="views"
    )

    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("story", "viewer")


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, unique=True)
    bio = models.TextField(blank=True)
    
    # THIS IS THE ONLY CHANGE — USE ImageField, NOT URLField
    profile_image = models.ImageField(
        upload_to='profile_pics/',   # Saves to media/profile_pics/
        blank=True,
        null=True,
        default='profile_pics/default.jpg'  # Optional: add a default avatar
    )
    
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following')
    anime_board = models.JSONField(default=dict)

    def __str__(self):
        return self.username


# models.py

class Post(models.Model):

    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('followers', 'Followers Only'),
    ]

    POST_TYPE_CHOICES = [
        ('image', 'Image Post'),
        ('thought', 'Thought'),
    ]

    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='posts'
    )

    # 🔹 NEW FIELD (determines post type)
    post_type = models.CharField(
        max_length=10,
        choices=POST_TYPE_CHOICES,
        default='image'
    )

    # 🔹 Image optional now
    image = models.ImageField(
        upload_to='post_images/',
        blank=True,
        null=True
    )

    caption = models.TextField(
        max_length=2000,
        blank=True
    )

    # Anime tagging
    anime_id = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    anime_title = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    privacy = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='public'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.post_type == "thought":
            return f"{self.author.username} - Thought"

        return f"{self.author.username} - {self.anime_title or 'Image Post'}"


class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"
    


class PostComment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    post = models.ForeignKey(
        "Post",
        on_delete=models.CASCADE,
        related_name="comments"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} commented on Post {self.post.id}"
    

# models.py
class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user1 = models.ForeignKey(
        User,
        related_name='chat_rooms_as_user1',
        on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        User,
        related_name='chat_rooms_as_user2',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Chat: {self.user1} ↔ {self.user2}"
    


# api/models.py

class PostView(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="post_views"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="views"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")  # 🔥 IMPORTANT
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} viewed Post {self.post.id}"
    




class GroupChat(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=150,
        db_index=True  # 🔥 improves search performance
    )

    about = models.TextField(blank=True)

    # Anime tagging (optional, single anime)
    anime_id = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    anime_title = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to="group_images/",
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_groups"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        # 🔥 CASE-INSENSITIVE UNIQUE ONLY FOR ACTIVE GROUPS
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                condition=Q(is_active=True),
                name='unique_active_group_name_ci'
            )
        ]

    def save(self, *args, **kwargs):
        # 🔥 Always trim spaces
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class GroupMember(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("member", "Member"),
    )

    STATUS_CHOICES = (
        ("active", "Active"),
        ("pending", "Pending"),
    )

    group = models.ForeignKey(
        GroupChat,
        related_name="members",
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships"
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="member"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("group", "user")
        indexes = [
            models.Index(fields=["group"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} in {self.group} ({self.status})"
    


from django.conf import settings
from django.db import models


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ("follow", "Follow"),
        ("like", "Like"),
        ("comment", "Comment"),
        ("reply", "Reply"),
        ("dm", "Direct Message"),
        ("post", "New Post"),
        ("thought", "New Thought"),
    ]

    # ───────── CORE USERS ─────────

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications"
    )

    # ───────── TYPE ─────────

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )

    # ───────── OPTIONAL TARGETS ─────────

    # Used for like/comment/thought/post
    post = models.ForeignKey(
        "Post",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    # Used for replies (future safe)
    comment_id = models.IntegerField(
        null=True,
        blank=True
    )

    # Used for DM
    chat_room_id = models.UUIDField(
        null=True,
        blank=True
    )

    # Used for follow/profile navigation
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="targeted_notifications"
    )

    # ───────── CONTENT ─────────

    text = models.CharField(max_length=255, blank=True)

    # ───────── STATE ─────────

    is_read = models.BooleanField(default=False)

    # ───────── TIME ─────────

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.sender} → {self.recipient} ({self.notification_type})"


class DeviceToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="device_tokens"
    )
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.token[:10]}"