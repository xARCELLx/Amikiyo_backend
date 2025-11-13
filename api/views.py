from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer,PostSerializer
from rest_framework.authtoken.models import Token
import firebase_admin
from firebase_admin import auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class UserCreateView(APIView):
    authentication_classes = []  # Disable DRF auth
    permission_classes = []      # Disable permissions

    def post(self, request):
        print("\n=== USER CREATE REQUEST ===")
        print("HEADERS:", dict(request.headers))
        print("BODY:", request.data)
        print("ORIGIN:", request.META.get('HTTP_ORIGIN'))
        print("===========================\n")

        # === 1. Extract Bearer Token ===
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            print("Missing or invalid Authorization header")
            return Response(
                {'error': 'Missing Bearer token in Authorization header'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        id_token = auth_header.split('Bearer ')[1]
        print(f"Token preview: {id_token[:30]}...")

        # === 2. Verify Firebase Token ===
        try:
            decoded_token = auth.verify_id_token(id_token)
            print(f"Token verified! UID: {decoded_token['uid']}")
        except Exception as e:
            print(f"Token verification failed: {str(e)}")
            return Response(
                {'error': 'Invalid Firebase token', 'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        username = request.data.get('username', email.split('@')[0] if email else f"user_{firebase_uid[:8]}")

        print(f"Syncing user: UID={firebase_uid}, email={email}, username={username}")

        # === 3. Create or Get User ===
        user, user_created = User.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={
                'username': username,
                'email': email,
            }
        )

        if not user_created:
            # Update username if changed
            if user.username != username:
                user.username = username
                user.save()
            print(f"User already exists: {user.username}")

        # === 4. Create or Get Profile ===
        profile, profile_created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'username': user.username,
                'bio': '',
                'profile_image': '',
                'anime_board': {}
            }
        )

        # === 5. Create or Get DRF Token ===
        token, token_created = Token.objects.get_or_create(user=user)

        print(f"{'CREATED' if user_created else 'SYNCED'} user & profile")
        print(f"DRF Token: {token.key}")

        # === 6. Return Response ===
        return Response({
            'user': UserSerializer(user).data,
            'profile': ProfileSerializer(profile).data,
            'token': token.key,
            'created': user_created
        }, status=status.HTTP_201_CREATED if user_created else status.HTTP_200_OK)

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
        

class PostCreateView(APIView):
    def post(self, request):
        try:
            # Verify Firebase JWT for authentication
            id_token = request.headers.get('Authorization').split('Bearer ')[1]
            decoded_token = auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']

            # Get or create user based on Firebase UID
            user = User.objects.get(firebase_uid=firebase_uid)
            profile = Profile.objects.get(user=user)

            # Validate and save post data
            serializer = PostSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=profile)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Profile.DoesNotExist:
        return Response(
            {'error': 'Profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )