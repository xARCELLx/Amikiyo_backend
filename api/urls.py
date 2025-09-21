from django.urls import path
from .views import UserCreateView, UserProfileView, PostCreateView

urlpatterns = [
    path('users/', UserCreateView.as_view(), name='user-create'),
    path('users/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
    path('posts/', PostCreateView.as_view(), name='post-create'),
]