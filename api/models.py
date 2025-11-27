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

    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='post_images/')
    caption = models.TextField(max_length=500, blank=True)

    # REPLACE ForeignKey WITH THESE TWO FIELDS
    anime_id = models.CharField(max_length=20, blank=True, null=True)      # stores "12345"
    anime_title = models.CharField(max_length=200, blank=True, null=True)  # stores "Attack on Titan"

    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username} - {self.anime_title or 'No Anime'}"