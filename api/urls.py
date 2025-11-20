from django.urls import path
from .views import UserCreateView, UserProfileView, PostCreateView ,get_my_profile


urlpatterns = [
    path('users/', UserCreateView.as_view(), name='user-create'),
    path('users/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
    path('posts/', PostCreateView.as_view(), name='post-create'),
    path('profiles/me/',get_my_profile , name='my-profile'),
]