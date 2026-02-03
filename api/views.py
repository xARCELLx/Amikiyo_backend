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
from .serializers import ProfileSerializer, PostSerializer
from firebase_admin import auth

from .models import ChatRoom, User,PostComment
from .serializers import ChatRoomSerializer,PostCommentSerializer



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

