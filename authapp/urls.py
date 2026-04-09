from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from .views import (
    SignupView, VerifyOTPView, ResendOTPView, LoginView,
    LogoutView, ForgotPasswordView, ResetPasswordView
)

app_urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]

schema_view = get_schema_view(
    openapi.Info(
        title='Auth API',
        default_version='v1',
        description='Authentication and account endpoints.',
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[path('auth/', include(app_urlpatterns))],
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='auth-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='auth-swagger-json'),
] + app_urlpatterns