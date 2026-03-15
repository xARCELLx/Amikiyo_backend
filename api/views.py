# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.authtoken.models import Token

from .models import Profile, Post,User,Post, PostLike
from .serializers import ProfileSerializer, PostSerializer,FeedPostSerializer
from firebase_admin import auth

from .models import ChatRoom, User,PostComment,PostView
from .serializers import ChatRoomSerializer,PostCommentSerializer


from django.db.models import Count, F, ExpressionWrapper, FloatField,Q,DurationField
from django.db.models.functions import Now
from django.utils.timezone import now
from django.db.models.functions import Now,Cast
from .models import GroupChat, GroupMember
from .models import Story, StoryView
from .serializers import StorySerializer
from django.utils import timezone
from datetime import timedelta


from .serializers import (
    CreateGroupSerializer,
    GroupChatSerializer
)
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


User = get_user_model()



class CreateGroupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        member_ids = request.data.get("member_ids")

        # 🔥 Handle JSON string from multipart safely
        if isinstance(member_ids, str):
            import json
            try:
                member_ids = json.loads(member_ids)
            except Exception:
                return Response(
                    {"member_ids": "Invalid format."},
                    status=400
                )

        # 🔥 Build clean data dict manually (no copy())
        serializer = CreateGroupSerializer(data={
            "name": request.data.get("name"),
            "about": request.data.get("about", ""),
            "anime_id": request.data.get("anime_id"),
            "anime_title": request.data.get("anime_title"),
            "member_ids": member_ids or [],
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        validated = serializer.validated_data

        # 🔥 Create group
        group = GroupChat.objects.create(
            name=validated["name"],
            about=validated.get("about", ""),
            anime_id=validated.get("anime_id"),
            anime_title=validated.get("anime_title"),
            created_by=request.user,
            image=request.FILES.get("image")
        )

        # 🔥 Add creator as admin
        GroupMember.objects.create(
            group=group,
            user=request.user,
            role="admin"
        )

        # 🔥 Add members
        users = User.objects.filter(id__in=validated["member_ids"])

        for user in users:
            if user != request.user:
                GroupMember.objects.create(
                    group=group,
                    user=user,
                    role="member"
                )

        return Response(
            GroupChatSerializer(group).data,
            status=status.HTTP_201_CREATED
        )

class MyGroupsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = GroupChat.objects.filter(
        members__user=request.user,
        members__is_active=True,
        members__status="active",
        is_active=True
    ).distinct()


        serializer = GroupChatSerializer(groups, many=True)
        return Response(serializer.data)


class GroupDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, group_id):
        return get_object_or_404(
            GroupChat,
            id=group_id,
            is_active=True
        )

    def get(self, request, group_id):
        group = self.get_object(group_id)

        is_member = GroupMember.objects.filter(
            group=group,
            user=request.user,
            is_active=True
        ).exists()

        if not is_member:
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = GroupChatSerializer(group)
        return Response(serializer.data)

    @transaction.atomic
    def delete(self, request, group_id):
        group = self.get_object(group_id)

        admin = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
            is_active=True
        ).first()

        if not admin:
            raise PermissionDenied("Only admin can delete group.")

        group.is_active = False
        group.save()

        return Response({"detail": "Group deleted successfully."})


class AddMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(GroupChat, id=group_id, is_active=True)

        # Check admin
        membership = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
            is_active=True
        ).first()

        if not membership:
            raise PermissionDenied("Only admin can add members.")

        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id required."}, status=400)

        user = get_object_or_404(User, id=user_id)

        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={
                "role": "member",
                "is_active": True,
                "status": "active",
            }
        )

        # 🔥 If user existed but was inactive, reactivate properly
        if not created:
            member.is_active = True
            member.status = "active"
            member.role = "member"
            member.save()
            return Response({"detail": "Member reactivated."})

        return Response({"detail": "Member added successfully."})

    

class RemoveMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(GroupChat, id=group_id, is_active=True)

        admin = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
            is_active=True
        ).first()

        if not admin:
            raise PermissionDenied("Only admin can remove members.")

        user_id = request.data.get("user_id")

        member = get_object_or_404(
            GroupMember,
            group=group,
            user__id=user_id,
            is_active=True
        )

        if member.user == request.user:
            return Response({"detail": "Use leave endpoint."}, status=400)

        member.is_active = False
        member.save()

        return Response({"detail": "Member removed."})
    

class TransferAdminAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(GroupChat, id=group_id, is_active=True)

        # Check requester is active admin
        current_admin = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
            is_active=True
        ).first()

        if not current_admin:
            raise PermissionDenied("Only admin can transfer ownership.")

        new_admin_id = request.data.get("user_id")
        if not new_admin_id:
            return Response({"detail": "user_id required."}, status=400)

        new_admin_member = get_object_or_404(
            GroupMember,
            group=group,
            user__id=new_admin_id,
            is_active=True
        )

        # Demote current admin
        current_admin.role = "member"
        current_admin.save()

        # Promote new admin
        new_admin_member.role = "admin"
        new_admin_member.save()

        return Response({"detail": "Admin transferred successfully."})

class LeaveGroupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(GroupChat, id=group_id, is_active=True)

        member = get_object_or_404(
            GroupMember,
            group=group,
            user=request.user,
            is_active=True
        )

        # If admin, ensure another admin exists
        if member.role == "admin":
            other_admin_exists = GroupMember.objects.filter(
                group=group,
                role="admin",
                is_active=True
            ).exclude(user=request.user).exists()

            if not other_admin_exists:
                return Response(
                    {"detail": "Transfer admin before leaving."},
                    status=400
                )

        member.is_active = False
        member.save()

        return Response({"detail": "Left group successfully."})
    
class ValidateGroupMembershipAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        is_member = GroupMember.objects.filter(
            group__id=group_id,
            user=request.user,
            is_active=True,
            status="active",
            group__is_active=True
        ).exists()

        return Response({
            "allowed": is_member
        })
    


class SearchGroupsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response([])

        groups = GroupChat.objects.filter(
            name__icontains=query,
            is_active=True
        )

        data = []
        for group in groups:
            membership = GroupMember.objects.filter(
                group=group,
                user=request.user
            ).first()

            status_value = None
            if membership:
                status_value = membership.status

            data.append({
                "id": str(group.id),
                "name": group.name,
                "image": group.image.url if group.image else None,
                "membership_status": status_value  # active / pending / None
            })

        return Response(data)

class RequestJoinGroupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(
            GroupChat,
            id=group_id,
            is_active=True
        )

        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={
                "role": "member",
                "status": "pending"
            }
        )

        if not created:
            if member.status == "active":
                return Response(
                    {"detail": "Already a member."},
                    status=400
                )
            elif member.status == "pending":
                return Response(
                    {"detail": "Request already pending."},
                    status=400
                )

        return Response({
            "detail": "Join request sent."
        })


class ApproveJoinRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(GroupChat, id=group_id)

        # Check admin
        admin = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
            status="active",
            is_active=True
        ).exists()

        if not admin:
            raise PermissionDenied("Only admin can approve.")

        user_id = request.data.get("user_id")

        member = get_object_or_404(
            GroupMember,
            group=group,
            user__id=user_id,
            status="pending"
        )

        member.status = "active"
        member.save()

        return Response({"detail": "User approved."})


class RejectJoinRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, group_id):
        group = get_object_or_404(GroupChat, id=group_id)

        admin = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
            status="active",
            is_active=True
        ).exists()

        if not admin:
            raise PermissionDenied("Only admin can reject.")

        user_id = request.data.get("user_id")

        GroupMember.objects.filter(
            group=group,
            user__id=user_id,
            status="pending"
        ).delete()

        return Response({"detail": "Request rejected."})
    


class UpdateGroupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, group_id):

        group = get_object_or_404(
            GroupChat,
            id=group_id,
            is_active=True
        )

        # 🔥 Only admin can update
        membership = GroupMember.objects.filter(
            group=group,
            user=request.user,
            role="admin",
            is_active=True
        ).first()

        if not membership:
            raise PermissionDenied("Only admin can update group.")

        name = request.data.get("name")
        about = request.data.get("about")
        anime_id = request.data.get("anime_id")
        anime_title = request.data.get("anime_title")

        # ───────── NAME VALIDATION ─────────

        if name is not None:
            name = name.strip()

            if not name:
                return Response(
                    {"name": "Group name cannot be empty."},
                    status=400
                )

            # 🔥 Check uniqueness excluding self
            exists = GroupChat.objects.filter(
                name__iexact=name
            ).exclude(id=group.id).exists()

            if exists:
                return Response(
                    {"name": "Group name already exists."},
                    status=400
                )

            group.name = name

        # ───────── ABOUT ─────────

        if about is not None:
            group.about = about.strip()

        # ───────── ANIME ─────────

        if anime_id is not None:
            group.anime_id = anime_id

        if anime_title is not None:
            group.anime_title = anime_title

        # ───────── IMAGE ─────────

        if "image" in request.FILES:
            group.image = request.FILES["image"]

        group.save()

        return Response(
            GroupChatSerializer(group).data,
            status=status.HTTP_200_OK
        )






# ====================== USER CREATION (UNCHANGED — PERFECT) ======================
@method_decorator(csrf_exempt, name='dispatch')
class UserCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': 'Missing Bearer token'}, status=status.HTTP_401_UNAUTHORIZED)

        id_token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            print("🔥 FIREBASE VERIFY ERROR:", str(e))
            return Response({'error': str(e)}, status=401)
        

        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        username = request.data.get('username', email.split('@')[0] if email else f"user_{firebase_uid[:8]}")

        user, created = User.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={'username': username, 'email': email}
        )
        if not created and user.username != username:
            user.username = username
            user.save()

        profile, _ = Profile.objects.get_or_create(user=user, defaults={'username': user.username})
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user': {'id': user.id, 'username': user.username},
            'profile': ProfileSerializer(profile, context={'request': request}).data,
            'token': token.key,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# ====================== MY PROFILE — FULL URL SUPPORT ======================
@api_view(['GET', 'PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================== PUBLIC PROFILE (UNCHANGED) ======================
class UserProfileView(APIView):
    def get(self, request, user_id):
        try:
            profile = Profile.objects.get(user__id=user_id)
            serializer = ProfileSerializer(profile, context={'request': request})
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


# ====================== POST CREATION (AUTO CONTEXT — NO CHANGE NEEDED) ======================
class PostCreateView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """
        Ensures serializer has access to request
        (needed for absolute URLs and like checks)
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        """
        Automatically attach the author's profile
        """
        serializer.save(author=self.request.user.profile)

# ====================== MY POSTS — FULL URL SUPPORT ======================
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_my_posts(request):
    profile = request.user.profile
    posts = profile.posts.all().order_by('-created_at')[:20]
    serializer = PostSerializer(posts, many=True, context={'request': request})  # CONTEXT ADDED
    return Response(serializer.data)


# ====================== POST DELETE — THIS WAS MISSING ======================
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_post(request, pk):
    try:
        post = Post.objects.get(id=pk, author=request.user.profile)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found or not yours'}, status=status.HTTP_404_NOT_FOUND)

    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_users(request):
    query = request.query_params.get('username', '').strip()
    if not query:
        return Response([], status=status.HTTP_200_OK)

    # Explicit case-insensitive search
    profiles = Profile.objects.filter(username__iexact=query) | Profile.objects.filter(username__icontains=query)
    profiles = profiles.distinct()[:10]  # limit 10 results

    serializer = ProfileSerializer(profiles, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ====================== OTHER USER PROFILE ======================
class PublicProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            profile = Profile.objects.get(user__id=pk)
            serializer = ProfileSerializer(profile, context={'request': request})
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        


# ====================== OTHER USER POSTS (PUBLIC SAFE) ======================
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_user_posts(request, user_id):
    try:
        profile = Profile.objects.get(user__id=user_id)
    except Profile.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    viewer = request.user.profile

    posts = Post.objects.filter(author=profile).order_by('-created_at')

    # 🔒 PRIVACY RULES
    if viewer != profile:
        posts = posts.filter(privacy='public')

    serializer = PostSerializer(
        posts,
        many=True,
        context={'request': request}
    )
    return Response(serializer.data)




# views.py




class GetOrCreateChatRoom(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        other_user_id = request.data.get('user_id')

        if not other_user_id:
            return Response(
                {'error': 'user_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        me = request.user

        # 🔥 ORDER USERS (CRITICAL FIX)
        user1, user2 = sorted(
            [me, other_user],
            key=lambda u: u.id
        )

        chat, _ = ChatRoom.objects.get_or_create(
            user1=user1,
            user2=user2
        )

        serializer = ChatRoomSerializer(
            chat,
            context={'request': request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class MyChatRooms(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        me = request.user

        chats = ChatRoom.objects.filter(
            user1=me
        ) | ChatRoom.objects.filter(
            user2=me
        )

        serializer = ChatRoomSerializer(
            chats.order_by('-created_at'),
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)
    



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    try:
        me = request.user.profile
        target = Profile.objects.get(user__id=user_id)

        if me == target:
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        me.following.add(target)
        target.followers.add(me)

        return Response({
            'followed': True,
            'followers_count': target.followers.count()
        })

    except Profile.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    try:
        me = request.user.profile
        target = Profile.objects.get(user__id=user_id)

        me.following.remove(target)
        target.followers.remove(me)

        return Response({
            'followed': False,
            'followers_count': target.followers.count()
        })

    except Profile.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# views.py

class FollowersList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            profile = Profile.objects.get(user__id=user_id)
        except Profile.DoesNotExist:
            return Response(status=404)

        data = [
            {
                'user_id': p.user.id,
                'username': p.username,
                'profile_image': request.build_absolute_uri(
                    p.profile_image.url
                ) if p.profile_image else None,
            }
            for p in profile.followers.all()
        ]

        return Response(data)


class FollowingList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            profile = Profile.objects.get(user__id=user_id)
        except Profile.DoesNotExist:
            return Response(status=404)

        data = [
            {
                'user_id': p.user.id,
                'username': p.username,
                'profile_image': request.build_absolute_uri(
                    p.profile_image.url
                ) if p.profile_image else None,
            }
            for p in profile.following.all()
        ]

        return Response(data)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=404)

    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post
    )

    return Response({
        "liked": True,
        "likes_count": post.likes.count()
    }, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unlike_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=404)

    PostLike.objects.filter(
        user=request.user,
        post=post
    ).delete()

    return Response({
        "liked": False,
        "likes_count": post.likes.count()
    }, status=200)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_comments(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=404)

    comments = PostComment.objects.filter(post=post)
    serializer = PostCommentSerializer(
        comments,
        many=True,
        context={"request": request}
    )

    return Response(serializer.data, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_comment(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=404)

    text = request.data.get("text", "").strip()
    if not text:
        return Response({"detail": "Comment cannot be empty"}, status=400)

    comment = PostComment.objects.create(
        user=request.user,
        post=post,
        text=text
    )

    serializer = PostCommentSerializer(
        comment,
        context={"request": request}
    )

    return Response(serializer.data, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"detail": "Comment not found"}, status=404)

    if comment.user != request.user:
        return Response(
            {"detail": "Not allowed"},
            status=status.HTTP_403_FORBIDDEN
        )

    comment.delete()
    return Response(status=204)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def home_feed(request):
    user_profile = request.user.profile

    following_profiles = user_profile.following.all()

    # STRICT PRIVACY FILTER
    posts = Post.objects.filter(
        Q(author=user_profile) |  # always see your own posts
        Q(author__in=following_profiles, privacy__in=["public", "followers"]) |
        Q(privacy="public")
    ).distinct()

    # ───────── COUNTS ─────────
    posts = posts.annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
        views_count=Count("views", distinct=True)
    )

    # ───────── PROPER RECENCY CALCULATION ─────────

    from django.db.models.functions import Now
    from django.db.models import DurationField
    from django.db.models.functions import Cast

    hours_since = ExpressionWrapper(
        (Now() - F("created_at")),
        output_field=DurationField()
    )

    posts = posts.annotate(
        hours_since_posted=Cast(hours_since, FloatField())
    )

    # Instead of broken ExtractHour math
    posts = posts.annotate(
        score=(
            F("likes_count") * 3 +
            F("comments_count") * 4 +
            F("views_count") * 1 +
            48 / (F("likes_count") + F("comments_count") + 2)
        )
    ).order_by("-score", "-created_at")

    serializer = PostSerializer(
        posts,
        many=True,
        context={"request": request}
    )

    return Response(serializer.data)


# ====================== RECORD POST VIEW ======================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def record_post_view(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"detail": "Post not found"}, status=404)

    viewer = request.user

    # 🔒 PRIVACY CHECK
    author_profile = post.author
    viewer_profile = viewer.profile

    if author_profile != viewer_profile:
        if post.privacy == "followers":
            if viewer_profile not in author_profile.followers.all():
                return Response(
                    {"detail": "This post is private"},
                    status=403
                )

    # 🔥 UNIQUE VIEW LOGIC
    PostView.objects.get_or_create(
        user=viewer,
        post=post
    )

    return Response({"view_recorded": True}, status=200)



class PostDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"detail": "Post not found"}, status=404)

        # 🔒 PRIVACY CHECK
        viewer_profile = request.user.profile
        author_profile = post.author

        if author_profile != viewer_profile:
            if post.privacy == "followers":
                if viewer_profile not in author_profile.followers.all():
                    return Response(
                        {"detail": "This post is private"},
                        status=403
                    )

        serializer = PostSerializer(
            post,
            context={"request": request}
        )

        return Response(serializer.data)
    


class CreateStoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        image = request.FILES.get("image")

        if not image:
            return Response({"error": "Image required"}, status=400)

        story = Story.objects.create(
            user=request.user,
            image=image
        )

        return Response(StorySerializer(story, context={"request": request}).data)
    




class StoryFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        now = timezone.now()
        limit = now - timedelta(hours=24)

        active_stories = Story.objects.filter(
            created_at__gte=limit
        ).select_related("user", "user__profile")

        stories_by_user = {}

        for story in active_stories:

            user = story.user
            user_id = user.id

            # SAFE PROFILE IMAGE URL
            profile_image = None
            if hasattr(user, "profile") and user.profile.profile_image:
                profile_image = request.build_absolute_uri(
                    user.profile.profile_image.url
                )

            if user_id not in stories_by_user:
                stories_by_user[user_id] = {
                "user_id": story.user.id,
                "username": story.user.username,
                "profile_image": (
                    request.build_absolute_uri(story.user.profile.profile_image.url)
                    if getattr(story.user.profile, "profile_image", None)
                    else None
                ),
                "is_me": story.user == request.user,
                "stories": []
            }

            serializer = StorySerializer(
                story,
                context={"request": request}
            )

            stories_by_user[user_id]["stories"].append(serializer.data)

        return Response(list(stories_by_user.values()))

class ViewStory(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):

        try:
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response({"error": "Story not found"}, status=404)

        StoryView.objects.get_or_create(
            story=story,
            viewer=request.user
        )

        return Response({"status": "view recorded"})
    

class MyStoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        now = timezone.now()
        limit = now - timedelta(hours=24)

        stories = Story.objects.filter(
            user=request.user,
            created_at__gte=limit
        )

        serializer = StorySerializer(
            stories,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)
    
class DeleteStory(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, story_id):

        try:
            story = Story.objects.get(id=story_id, user=request.user)
        except Story.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        story.delete()

        return Response({"status": "deleted"})
        

class StoryViewers(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, story_id):

        try:
            story = Story.objects.get(id=story_id, user=request.user)
        except Story.DoesNotExist:
            return Response({"error": "Not allowed"}, status=403)

        viewers = StoryView.objects.filter(story=story).select_related("viewer")

        data = []

        for v in viewers:
            profile = getattr(v.viewer, "profile", None)

            data.append({
                "username": v.viewer.username,
                "profile_image": (
                    request.build_absolute_uri(profile.profile_image.url)
                    if profile and profile.profile_image else None
                )
            })

        return Response(data)