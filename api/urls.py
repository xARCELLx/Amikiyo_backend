# api/urls.py (or wherever your urlpatterns are)

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    UserCreateView,
    UserProfileView,
    PostCreateView,
    get_my_profile,
    get_my_posts,
)

urlpatterns = [
    path('users/', UserCreateView.as_view(), name='user-create'),
    path('users/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
    path('posts/', PostCreateView.as_view(), name='post-create'),
    path('profiles/me/', get_my_profile, name='my-profile'),
    path('posts/user/me/', get_my_posts, name='my-posts'),
]

# THIS IS THE ONLY THING THAT WAS MISSING — ADD THIS AT THE END
# Serves media files (profile pics, post images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)