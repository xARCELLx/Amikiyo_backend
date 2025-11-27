# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Profile, Post
from .serializers import ProfileSerializer, PostSerializer
from firebase_admin import auth


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