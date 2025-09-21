from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    firebase_uid = models.CharField(max_length=128, unique=True, null=True)

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, unique=True)
    bio = models.TextField(blank=True)
    profile_image = models.URLField(blank=True)  # Firebase Storage URL
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following')
    anime_board = models.JSONField(default=dict)  # Top 3, watched, next-to-watch

    def __str__(self):
        return self.username

class Post(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    image_url = models.URLField()  # Firebase Storage URL
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Post by {self.user.username}'