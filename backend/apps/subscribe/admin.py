from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import SubscriptionPlan, Subscription, SubscriptionHistory


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active', 'subscriptions_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'duration_days')
        }),
        ('Features', {
            'fields': ('features',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def subscriptions_count(self, obj):
        return obj.subscriptions.count()
    subscriptions_count.short_description = 'Подписки'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('subscriptions')


class SubscriptionHistoryInline(admin.TabularInline):
    model = SubscriptionHistory
    extra = 0
    readonly_fields = ('action', 'description', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'plan', 'status', 'is_active_display', 'days_remaining_display', 'start_date', 'end_date')
    list_filter = ('status', 'plan', 'auto_renew', 'created_at')
    search_fields = ('user__username', 'user__email', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'is_active')
    raw_id_fields = ('user',)
    inlines = [SubscriptionHistoryInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'plan', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'auto_renew')
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Активна</span>')
        else:
            return format_html('<span style="color: red;">✗ Неактивна</span>')
    is_active_display.short_description = 'Активность'

    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days > 7:
            color = 'green'
        elif days > 0:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{} дн.</span>', color, days)
    days_remaining_display.short_description = 'Осталось дней'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'plan')


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ('subscription_link', 'action', 'description_short', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('subscription__user__username', 'description')
    readonly_fields = ('subscription', 'action', 'description', 'created_at')
    
    def subscription_link(self, obj):
        url = reverse('admin:subscribe_subscription_change', args=[obj.subscription.pk])
        return format_html('<a href="{}">{} - {}</a>', url, obj.subscription.user.username, obj.subscription.plan.name)
    subscription_link.short_description = 'Подписка'

    def description_short(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Описание'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription', 'subscription__user')
