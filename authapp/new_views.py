from django.contrib.auth import get_user_model
from django.core import signing
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from coreapp.mixins import StandardResponseMixin, extract_first_error

from .new_serializers import (
    NewRefreshAccessTokenSerializer,
    NewResetPasswordNoTokenSerializer,
    NewVerifyOTPSerializer,
    RESET_SECRET_SALT,
)

User = get_user_model()


class NewVerifyOTPView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = NewVerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Verification failed: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        otp = serializer.validated_data["otp"]
        user = User.objects.get(email=serializer.validated_data["email"])

        user.verified = True
        user.save(update_fields=["verified", "updated_at"])

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        secret_key = signing.dumps(
            {
                "purpose": "new_reset_password",
                "user_email": serializer.validated_data["email"],
            },
            salt=RESET_SECRET_SALT,
        )

        return self.success_response(
            {"secret_key": secret_key},
            message="Token verified successfully.",
            status_code=200,
        )


class NewResetPasswordNoTokenView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = NewResetPasswordNoTokenSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Password reset failed: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        user = serializer.validated_data["user"]
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        return self.success_response(
            {},
            message="Password reset successful.",
            status_code=200,
        )


class NewAccessTokenFromRefreshView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = NewRefreshAccessTokenSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Access token generation failed: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        refresh_value = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_value)
            access = str(token.access_token)
        except TokenError:
            return self.error_response(
                "Invalid or expired refresh token.",
                status_code=400,
            )

        return self.success_response(
            {"access": access},
            message="Access token generated successfully.",
            status_code=200,
        )
