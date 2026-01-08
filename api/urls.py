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
    delete_post,
    search_users,
    PublicProfileView,
    login_view
)

urlpatterns = [
    path('users/', UserCreateView.as_view(), name='user-create'),
    path('auth/login/', login_view, name='login'),
    path('users/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
    path('posts/', PostCreateView.as_view(), name='post-create'),
    path('profiles/me/', get_my_profile, name='my-profile'),
    path('posts/user/me/', get_my_posts, name='my-posts'),
    path('posts/<int:pk>/', delete_post, name='post-delete'),
    path('profiles/search/', search_users, name='search-users'),
    path('profiles/<int:pk>/', PublicProfileView.as_view(), name='public-profile'),
]

# THIS IS THE ONLY THING THAT WAS MISSING — ADD THIS AT THE END
# Serves media files (profile pics, post images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)