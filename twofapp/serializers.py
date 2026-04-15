import random
import string
from rest_framework import serializers
from .models import ParentalControl

class TwoFASendSerializer(serializers.Serializer):
    """User provides an email address to receive the 2FA OTP."""
    email = serializers.EmailField()
 
    def validate_email(self, value):
        return value.lower().strip()
 
 
class TwoFAVerifySerializer(serializers.Serializer):
    """User verifies OTP to complete 2FA setup."""
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
 
    def validate_email(self, value):
        return value.lower().strip()




class ParentalControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentalControl
        fields = ['related_email', 'relation_type']