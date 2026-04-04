# profileapp/urls.py
 
from django.urls import path
from .views import ProfileView, ProfileSetupView, ActivityUpdateView
 
urlpatterns = [
    path('setup/', ProfileSetupView.as_view(), name='profile-setup'),
    path('', ProfileView.as_view(), name='profile'),
    path('activity/', ActivityUpdateView.as_view(), name='profile-activity'),
]