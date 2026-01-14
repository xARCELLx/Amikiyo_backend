from rest_framework import serializers
from .models import User, Profile, Post,ChatRoom

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'firebase_uid', 'username', 'email']


# serializers.py

from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user_id',  
            'id','username', 'bio', 'profile_image', 'anime_board',
            'followers_count', 'following_count', 'posts_count',
        ]
        extra_kwargs = {
            'username': {'required': False},
            'bio': {'required': False},
            'anime_board': {'required': False},
        }

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_posts_count(self, obj):
        return obj.posts.count()

    # THIS IS THE MAGIC — FULL ABSOLUTE URL FOR PFP
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and data.get('profile_image'):
            data['profile_image'] = request.build_absolute_uri(data['profile_image'])
        return data

# serializers.py

from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_pfp = serializers.ImageField(source='author.profile_image', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_username', 'author_pfp',
            'image', 'caption', 'anime_id', 'anime_title',
            'privacy', 'created_at'
        ]
        read_only_fields = ['author', 'created_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user.profile
        return super().create(validated_data)

    # FULL ABSOLUTE URLS FOR POST IMAGE + AUTHOR PFP
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            # Post image
            if data.get('image'):
                data['image'] = request.build_absolute_uri(data['image'])
            # Author PFP
            if data.get('author_pfp'):
                data['author_pfp'] = request.build_absolute_uri(data['author_pfp'])
        return data
    

class ChatRoomSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'other_user', 'created_at']

    def get_other_user(self, obj):
        request = self.context.get('request')
        if not request:
            return None

        me = request.user
        other = obj.user2 if obj.user1 == me else obj.user1

        return {
            'id': other.id,
            'username': other.username,
        }