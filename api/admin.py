from django.contrib import admin
from .models import User, Profile, Post, PostComment


# ───────────────── USER ADMIN ─────────────────

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'firebase_uid')
    search_fields = ('username', 'email', 'firebase_uid')


# ───────────────── PROFILE ADMIN ─────────────────

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'bio', 'followers_count')
    search_fields = ('username', 'bio')
    filter_horizontal = ('followers',)

    def followers_count(self, obj):
        return obj.followers.count()

    followers_count.short_description = 'Followers Count'


# ───────────────── COMMENT INLINE (FOR POSTS) ─────────────────

class PostCommentInline(admin.TabularInline):
    model = PostComment
    extra = 0
    readonly_fields = ('user', 'text', 'created_at')
    ordering = ('created_at',)


# ───────────────── POST ADMIN ─────────────────

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'anime_title',
        'caption_preview',
        'privacy',
        'created_at',
    )

    search_fields = (
        'author__username',
        'caption',
        'anime_title',
    )

    list_filter = (
        'privacy',
        'created_at',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = ('-created_at',)

    inlines = [PostCommentInline]

    def caption_preview(self, obj):
        if obj.caption:
            return obj.caption[:50] + '...' if len(obj.caption) > 50 else obj.caption
        return '-'

    caption_preview.short_description = 'Caption'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')


# ───────────────── POST COMMENT ADMIN ─────────────────

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'post',
        'user',
        'short_text',
        'created_at',
    )

    search_fields = (
        'text',
        'user__username',
        'post__id',
    )

    list_filter = (
        'created_at',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = ('-created_at',)

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'Comment'
