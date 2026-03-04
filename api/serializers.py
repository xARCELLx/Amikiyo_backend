from rest_framework import serializers
from .models import User, Profile, Post,ChatRoom,PostComment
from django.contrib.auth import get_user_model
from .models import GroupChat, GroupMember



from rest_framework import serializers
from .models import Story


class StorySerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username", read_only=True)
    profile_image = serializers.CharField(source="user.profile.profile_image", read_only=True)

    views_count = serializers.SerializerMethodField()
    is_seen = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            "id",
            "image",
            "created_at",
            "username",
            "profile_image",
            "views_count",
            "is_seen"
        ]

    def get_views_count(self, obj):
        return obj.views.count()

    def get_is_seen(self, obj):
        user = self.context["request"].user
        return obj.views.filter(viewer=user).exists()
    
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'firebase_uid', 'username', 'email']


# serializers.py

from rest_framework import serializers
from .models import Profile


# serializers.py

from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    # ─── CORE FIELDS ─────────────────────────────
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()

    # 🔥 FOLLOW SYSTEM
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user_id',
            'id',
            'username',
            'bio',
            'profile_image',
            'anime_board',
            'followers_count',
            'following_count',
            'posts_count',
            'is_following',        # ✅ ADDED (NON-BREAKING)
        ]
        extra_kwargs = {
            'username': {'required': False},
            'bio': {'required': False},
            'anime_board': {'required': False},
        }

    # ─── COUNTS ─────────────────────────────

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_posts_count(self, obj):
        return obj.posts.count()

    # ─── FOLLOW STATUS ─────────────────────────────

    def get_is_following(self, obj):
        """
        Returns True if the requesting user follows this profile
        Safe for:
        - unauthenticated requests
        - self profile
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            me = request.user.profile
            return obj in me.following.all()
        except Exception:
            return False

    # ─── ABSOLUTE PROFILE IMAGE URL ─────────────────

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and data.get('profile_image'):
            data['profile_image'] = request.build_absolute_uri(
                data['profile_image']
            )

        return data


# serializers.py

from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_pfp = serializers.ImageField(source='author.profile_image', read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()

    
    author_user_id = serializers.IntegerField(
        source='author.user.id',
        read_only=True
    )

    author_username = serializers.CharField(
        source='author.username',
        read_only=True
    )

    class Meta:
        model = Post
        fields = [
            'author_user_id',      # 🔥 THIS
            'author_username', 
            'id', 'author', 'author_username', 'author_pfp',
            'image', 'caption', 'anime_id', 'anime_title',
            'privacy', 'created_at',
            "likes_count",
            "is_liked",
            "comments_count",
            "views_count",
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
    
    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return obj.likes.filter(user=request.user).exists()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_views_count(self, obj):
        return obj.views.count()

    

class PostCommentSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    profile_image = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = [
            "id",
            "user_id",
            "username",
            "profile_image",
            "text",
            "created_at",
            "is_owner",
        ]

    def get_profile_image(self, obj):
        profile = getattr(obj.user, "profile", None)
        if profile and profile.profile_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(profile.profile_image.url)
            return profile.profile_image.url
        return None

    def get_is_owner(self, obj):
        request = self.context.get("request")
        if request is None:
            return False
        return request.user == obj.user
    

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



class FeedPostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "image",
            "caption",
            "anime_title",
            "privacy",
            "created_at",
            "author",
            "likes_count",
            "comments_count",
            "views_count",
            "is_liked",
        ]

    def get_author(self, obj):
        return {
            "id": obj.author.user.id,
            "username": obj.author.user.username,
            "profile_image": obj.author.profile_image,
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_views_count(self, obj):
        return obj.views.count()

    def get_is_liked(self, obj):
        user = self.context["request"].user
        return obj.likes.filter(user=user).exists()


User = get_user_model()


class GroupMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")

    class Meta:
        model = GroupMember
        fields = [
            "user_id",
            "username",
            "role",
            "joined_at",
        ]



class GroupChatSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = GroupChat
        fields = [
            "id",
            "name",
            "about",
            "anime_id",
            "anime_title",
            "image",
            "created_by",
            "created_at",
            "members",
            "members_count",
        ]

    def get_members(self, obj):
        active_members = obj.members.filter(
            is_active=True,
            status="active"
        )

        return GroupMemberSerializer(
            active_members,
            many=True,
            context=self.context
        ).data

    def get_members_count(self, obj):
        return obj.members.filter(
            is_active=True,
            status="active"
        ).count()



class CreateGroupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    about = serializers.CharField(
        required=False,
        allow_blank=True
    )

    anime_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    anime_title = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True
    )

    def validate_name(self, value):
        value = value.strip()

        if GroupChat.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Group name already exists.")

        return value

