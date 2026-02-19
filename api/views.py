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
        serializer = CreateGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data["name"]
        about = serializer.validated_data.get("about", "")
        anime_id = serializer.validated_data.get("anime_id")
        anime_title = serializer.validated_data.get("anime_title")
        member_ids = serializer.validated_data["member_ids"]

        group = GroupChat.objects.create(
            name=name,
            about=about,
            anime_id=anime_id,
            anime_title=anime_title,
            created_by=request.user
        )


        # Create group
        group = GroupChat.objects.create(
            name=name,
            created_by=request.user
        )

        # Add creator as admin
        GroupMember.objects.create(
            group=group,
            user=request.user,
            role="admin"
        )

        # Add additional members
        users = User.objects.filter(id__in=member_ids)

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

        # Check if requester is admin
        try:
            membership = GroupMember.objects.get(
                group=group,
                user=request.user,
                is_active=True
            )
        except GroupMember.DoesNotExist:
            raise PermissionDenied("Not a group member.")

        if membership.role != "admin":
            raise PermissionDenied("Only admin can add members.")

        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"detail": "user_id required."}, status=400)

        user = get_object_or_404(User, id=user_id)

        # Prevent duplicate
        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={"role": "member"}
        )

        if not created and member.is_active:
            return Response({"detail": "User already member."}, status=400)

        member.is_active = True
        member.save()

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

        # If admin, check if last admin
        if member.role == "admin":
            other_admins = GroupMember.objects.filter(
                group=group,
                role="admin",
                is_active=True
            ).exclude(user=request.user)

            if not other_admins.exists():
                # Promote oldest member
                oldest_member = GroupMember.objects.filter(
                    group=group,
                    is_active=True
                ).exclude(user=request.user).order_by("joined_at").first()

                if oldest_member:
                    oldest_member.role = "admin"
                    oldest_member.save()

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

        # Only admin can update
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

        if name is not None:
            group.name = name

        if about is not None:
            group.about = about

        if anime_id is not None:
            group.anime_id = anime_id

        if anime_title is not None:
            group.anime_title = anime_title

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
        except Exception:
            return Response({'error': 'Invalid Firebase token'}, status=status.HTTP_401_UNAUTHORIZED)

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

    def perform_create(self, serializer):
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
