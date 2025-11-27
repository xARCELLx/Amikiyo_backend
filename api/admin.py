# api/admin.py

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
    list_display = ('author', 'anime_title', 'caption_preview', 'privacy', 'created_at')  # FIXED: 'user' → 'author'
    search_fields = ('author__username', 'caption', 'anime_title')
    list_filter = ('created_at', 'privacy')
    readonly_fields = ('created_at',)

    def caption_preview(self, obj):
        """Show first 50 chars of caption"""
        return obj.caption[:50] + '...' if len(obj.caption) > 50 else obj.caption or '-'

    caption_preview.short_description = 'Caption'

    def get_queryset(self, request):
        """Optimize admin queries"""
        return super().get_queryset(request).select_related('author')