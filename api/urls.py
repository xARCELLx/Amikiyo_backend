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
    get_user_posts,
    GetOrCreateChatRoom,
    MyChatRooms,
    follow_user,
    unfollow_user,
    FollowersList,
    FollowingList,
    like_post,
    unlike_post,
    get_comments,
    add_comment,
    delete_comment,
    home_feed,
    record_post_view
   
)

urlpatterns = [
    path('users/', UserCreateView.as_view(), name='user-create'),
    path('users/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
    path('posts/', PostCreateView.as_view(), name='post-create'),
    path('profiles/me/', get_my_profile, name='my-profile'),
    path('posts/user/me/', get_my_posts, name='my-posts'),
    path('posts/<int:pk>/', delete_post, name='post-delete'),
    path('profiles/search/', search_users, name='search-users'),
    path('profiles/<int:pk>/', PublicProfileView.as_view(), name='public-profile'),
    path('posts/user/<int:user_id>/', get_user_posts),
    path('chat/get-or-create/', GetOrCreateChatRoom.as_view()),
    path('chat/my/', MyChatRooms.as_view()),
    path('profiles/<int:user_id>/follow/', follow_user),
    path('profiles/<int:user_id>/unfollow/', unfollow_user),
    path('profiles/<int:user_id>/followers/', FollowersList.as_view()),
    path('profiles/<int:user_id>/following/', FollowingList.as_view()),
    path("posts/<int:post_id>/like/", like_post),
    path("posts/<int:post_id>/unlike/", unlike_post),
    path("posts/<int:post_id>/comments/", get_comments),
    path("posts/<int:post_id>/comments/add/", add_comment),
    path("comments/<int:comment_id>/delete/", delete_comment),
    path("feed/", home_feed),
path("posts/<int:post_id>/view/", record_post_view),

]

# THIS IS THE ONLY THING THAT WAS MISSING — ADD THIS AT THE END
# Serves media files (profile pics, post images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)