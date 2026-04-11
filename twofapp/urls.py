# twofa/urls.py
 
from django.urls import path
from .views import TwoFASendOTPView, TwoFAVerifyView, TwoFAStatusView
 
urlpatterns = [
    path('send/', TwoFASendOTPView.as_view(), name='2fa-send'),
    path('verify/', TwoFAVerifyView.as_view(), name='2fa-verify'),
    path('status/', TwoFAStatusView.as_view(), name='2fa-status'),
]
 