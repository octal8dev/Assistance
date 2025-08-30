from django.contrib import admin
from .models import Bot, Session, Chat


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active')
    list_filter = ('is_active', 'user')
    search_fields = ('name', 'user__username')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('bot',)
    search_fields = ('bot__name',)


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'chat_id')
    search_fields = ('name', 'chat_id')
