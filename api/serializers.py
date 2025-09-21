from rest_framework import serializers
from .models import User, Profile, Post

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'firebase_uid', 'username', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['username', 'bio', 'profile_image', 'anime_board', 'followers_count', 'following_count', 'posts_count']

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