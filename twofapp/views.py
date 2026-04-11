from django.shortcuts import render
from coreapp.mixins import StandardResponseMixin,extract_first_error
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.core.mail import send_mail
from authapp.models import OTP
from profileapp.models import UserProfile
from .serializers import TwoFASendSerializer,TwoFAVerifySerializer
import random
import string
from django.utils import timezone
from datetime import timedelta

# Create your views here.

class TwoFASendOTPView(StandardResponseMixin, APIView):
    """
    POST /2fa/send/
    Body: { "email": "user@example.com" }
    Sends a 6-digit OTP to the provided email for 2FA verification.
    """
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        serializer = TwoFASendSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"2FA setup failed: {reason}", status_code=400)
 
        email = serializer.validated_data['email']
 
        # Generate fresh OTP — delete any unused previous ones
        otp_code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)
 
        OTP.objects.filter(email=email, is_used=False).delete()##❓❓❓why not user=requst.user passed here? how this line working
        OTP.objects.create(email=email, otp_code=otp_code, expires_at=expires_at)
 
        # Send OTP via email
        send_mail(
            subject="Your Two-Factor Authentication Code",
            message=(
                f"Your 2FA verification code is: {otp_code}\n"
                f"This code expires in 10 minutes.\n"
                f"If you did not request this, please ignore this email."
            ),
            from_email='noreply@studyapp.com',
            recipient_list=[email],
        )
 
        return self.success_response(##❓❓❓ is self contains this success and error response method, how?
            {"email": email},
            message="A verification code has been sent to your email. Please check your inbox.",
            status_code=200
        )


 
class TwoFAVerifyView(StandardResponseMixin, APIView):
    """
    POST /2fa/verify/
    Body: { "email": "...", "otp_code": "123456" }
    Verifies OTP and marks 2FA as enabled on the user's profile.
    """
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        serializer = TwoFAVerifySerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"2FA verification failed: {reason}", status_code=400)
 
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
 
        # Find a valid OTP for this email+code combo
        try:
            otp = OTP.objects.get(email=email, otp_code=otp_code, is_used=False)
        except OTP.DoesNotExist:
            return self.error_response(
                "The verification code is incorrect. Please check the code and try again.",
                status_code=400
            )
 
        if not otp.is_valid():
            return self.error_response(
                "The verification code has expired. Please request a new one.",
                status_code=400
            )
 
        # Mark OTP as used
        otp.is_used = True
        otp.save(update_fields=['is_used'])
 
        # Enable 2FA on profile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)##❓❓❓ why _ using here
        profile.two_factor_enabled = True
        profile.two_factor_verified_at = timezone.now()
        profile.save(update_fields=['two_factor_enabled', 'two_factor_verified_at'])
 
        return self.success_response(
            {
                "two_factor_enabled": True,
                "verified_at": profile.two_factor_verified_at.isoformat(),
            },
            message="Two-factor authentication has been successfully enabled on your account.",
            status_code=200
        )
 
 
class TwoFAStatusView(StandardResponseMixin, APIView):
    """
    GET /2fa/status/
    Returns current 2FA status for the logged-in user.
    Frontend shows "Already 2FA verified" if enabled = True.
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return self.success_response(
            {
                "two_factor_enabled": profile.two_factor_enabled,
                "verified_at": (
                    profile.two_factor_verified_at.isoformat()
                    if profile.two_factor_verified_at else None
                ),
            },
            message="2FA status fetched successfully."
        )
 
