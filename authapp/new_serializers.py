from django.contrib.auth import get_user_model
from django.core import signing
from rest_framework import serializers

from .utils import validate_and_get_otp

User = get_user_model()
RESET_SECRET_SALT = "authapp.new.reset.password"
RESET_SECRET_MAX_AGE_SECONDS = 10 * 60


class NewVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data["email"].lower().strip()
        otp_code = data["otp_code"].strip()

        otp = validate_and_get_otp(email, otp_code)
        data["email"] = email
        data["otp"] = otp
        return data


class NewResetPasswordNoTokenSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    secret_key = serializers.CharField(max_length=512)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        user_email = data["user_email"].lower().strip()
        secret_key = data["secret_key"].strip()

        try:
            user = User.objects.get(email=user_email, verified=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("No verified account found with this email.")

        try:
            payload = signing.loads(
                secret_key,
                salt=RESET_SECRET_SALT,
                max_age=RESET_SECRET_MAX_AGE_SECONDS,
            )
        except signing.SignatureExpired:
            raise serializers.ValidationError("Secret key has expired. Please verify OTP again.")
        except signing.BadSignature:
            raise serializers.ValidationError("Invalid secret key.")

        if payload.get("purpose") != "new_reset_password" or payload.get("user_email") != user_email:
            raise serializers.ValidationError("Invalid secret key.")

        data["user_email"] = user_email
        data["user"] = user
        return data


class NewRefreshAccessTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
