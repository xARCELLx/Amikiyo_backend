from django.contrib import admin
from .models import User, Profile, Post



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'firebase_uid')
    search_fields = ('username', 'email', 'firebase_uid')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'bio', 'followers_count')
    search_fields = ('username', 'bio')
    filter_horizontal = ('followers',)

    def followers_count(self, obj):
        return obj.followers.count()
    followers_count.short_description = 'Followers Count'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'caption', 'created_at')
    search_fields = ('caption',)
    list_filter = ('created_at',)