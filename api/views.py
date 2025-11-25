# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer, PostSerializer
from rest_framework.authtoken.models import Token
import firebase_admin
from firebase_admin import auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import logging
logger = logging.getLogger(__name__)


# ====================== USER CREATION (UNCHANGED) ======================
@method_decorator(csrf_exempt, name='dispatch')
class UserCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # ... your existing perfect code (no change needed)
        # (I'm keeping it exactly as you wrote it — it's flawless)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': 'Missing Bearer token'}, status=status.HTTP_401_UNAUTHORIZED)

        id_token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
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

        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={'username': user.username}
        )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user': UserSerializer(user).data,
            'profile': ProfileSerializer(profile).data,
            'token': token.key,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# ====================== MY PROFILE — NOW SUPPORTS PATCH ======================
@api_view(['GET', 'PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    """
    GET  → returns current user's profile
    PATCH → updates profile (username, bio, profile_image, anime_board)
    """
    try:
        profile = request.user.profile  # Thanks to TokenAuthentication
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        # partial=True allows updating only some fields (e.g. just anime_board)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================== PUBLIC PROFILE VIEW (UNCHANGED) ======================
class UserProfileView(APIView):
    def get(self, request, user_id):
        try:
            profile = Profile.objects.get(user__id=user_id)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, user_id):
        try:
            profile = Profile.objects.get(user__id=user_id)
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


# ====================== POST CREATION (UNCHANGED) ======================
class PostCreateView(APIView):
    def post(self, request):
        try:
            id_token = request.headers.get('Authorization').split('Bearer ')[1]
            decoded_token = auth.verify_id_token(id_token)
            user = User.objects.get(firebase_uid=decoded_token['uid'])
            profile = Profile.objects.get(user=user)

            serializer = PostSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=profile)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_my_posts(request):
    """
    GET: Returns current user's posts
    """
    profile = request.user.profile
    posts = profile.posts.all().order_by('-created_at')[:20]  # Last 20 posts
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)