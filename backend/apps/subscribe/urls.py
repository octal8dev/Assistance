from django.urls import path
from . import views

urlpatterns = [
    # Subscription plans
    path('plans/', views.SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('plans/<int:pk>/', views.SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),
    
    # User subscription
    path('my-subscription/', views.UserSubscriptionView.as_view(), name='my-subscription'),
    path('status/', views.subscription_status, name='subscription-status'),
    path('history/', views.SubscriptionHistoryView.as_view(), name='subscription-history'),
    path('cancel/', views.cancel_subscription, name='cancel-subscription'),
]
