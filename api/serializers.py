from rest_framework import serializers
from .models import User, Profile, Post

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'firebase_uid', 'username', 'email']


# serializers.py

from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    # THIS IS THE ONLY CORRECT WAY — forces full absolute URL
    profile_image = serializers.ImageField(
        use_url=True,                    # ← gives http://your-ip:8000/media/...
        required=False,
        allow_empty_file=False,          # prevents empty file errors
    )

    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count     = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'username',
            'bio',
            'profile_image',       # ← now returns FULL URL
            'anime_board',
            'followers_count',
            'following_count',
            'posts_count',
        ]
        extra_kwargs = {
            'username':    {'required': False},
            'bio':         {'required': False},
            'anime_board': {'required': False},
        }

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_posts_count(self, obj):
        return obj.posts.count()

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['image_url', 'caption', 'created_at']