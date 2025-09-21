from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer,PostSerializer
from rest_framework.authtoken.models import Token
import firebase_admin
from firebase_admin import auth

class UserCreateView(APIView):
    def post(self, request):
        try:
            id_token = request.headers.get('Authorization').split('Bearer ')[1]
            decoded_token = auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']
            email = decoded_token.get('email')

            user, created = User.objects.get_or_create(
                firebase_uid=firebase_uid,
                defaults={'username': request.data.get('username'), 'email': email}
            )

            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={'username': user.username, 'bio': '', 'profile_image': '', 'anime_board': {}}
            )

            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                'user': UserSerializer(user).data,
                'profile': ProfileSerializer(profile).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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