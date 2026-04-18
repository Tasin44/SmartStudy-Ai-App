from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from profileapp.models import UserProfile

from .models import TermsConditionSection

User = get_user_model()

DEFAULT_PLAN_CHOICES = ("monthly", "yearly")


class AdminUserListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    signup_date = serializers.DateTimeField(source="created_at", read_only=True)
    account_status = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    current_plan = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    expiry_date = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "image",
            "email",
            "signup_date",
            "account_status",
            "subscription_status",
            "current_plan",
            "start_date",
            "expiry_date",
        ]

    def _default_start_end(self):
        start_date = self.context.get("default_start_date")
        expiry_date = self.context.get("default_expiry_date")
        if not start_date or not expiry_date:
            start_date = timezone.now().date()
            expiry_date = start_date + timedelta(days=30)
        return start_date, expiry_date

    def get_name(self, obj):
        profile_name = getattr(getattr(obj, "profile", None), "name", "")
        if profile_name:
            return profile_name
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name or obj.username

    def get_image(self, obj):
        request = self.context.get("request")
        profile = getattr(obj, "profile", None)
        if profile and profile.image and request:
            return request.build_absolute_uri(profile.image.url)
        if profile and profile.image:
            return profile.image.url
        return None

    def get_account_status(self, obj):
        return "verified" if obj.verified else "not_verified"

    def get_subscription_status(self, obj):
        return "monthly"

    def get_current_plan(self, obj):
        return "monthly"

    def get_start_date(self, obj):
        start_date, _ = self._default_start_end()
        return start_date

    def get_expiry_date(self, obj):
        _, expiry_date = self._default_start_end()
        return expiry_date


class AdminUserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=150)
    image = serializers.ImageField(required=False, allow_null=True)
    verified = serializers.BooleanField(default=False)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Name cannot be blank.")
        return name

    def create(self, validated_data):
        image = validated_data.pop("image", None)
        name = validated_data.pop("name")
        email = validated_data["email"]

        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            verified=validated_data.get("verified", False),
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.name = name
        if image:
            profile.image = image
        profile.save()
        return user


class AdminUserUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    verified = serializers.BooleanField(required=False)
    subscription_status = serializers.ChoiceField(
        choices=DEFAULT_PLAN_CHOICES,
        required=False,
    )

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Name cannot be blank.")
        return cleaned

    def update(self, instance, validated_data):
        profile, _ = UserProfile.objects.get_or_create(user=instance)

        if "name" in validated_data:
            profile.name = validated_data["name"]
        if "image" in validated_data:
            profile.image = validated_data["image"]
        profile.save()

        if "verified" in validated_data:
            instance.verified = validated_data["verified"]
            instance.save(update_fields=["verified", "updated_at"])

        # subscription_status is accepted as placeholder input for future integration.
        return instance


class AdminSelfSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    image = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.EmailField(read_only=True)


class AdminSelfUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    email = serializers.EmailField(required=False)

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Name cannot be blank.")
        return cleaned


class AdminPasswordResetSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


class TermsConditionSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsConditionSection
        fields = [
            "id",
            "section_name",
            "description",
            "order",
            "created_at",
            "updated_at",
        ]

    def validate_section_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Section name cannot be blank.")
        return cleaned

    def validate_description(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Description cannot be blank.")
        return cleaned


class TermsConditionBulkCreateSerializer(serializers.Serializer):
    sections = TermsConditionSectionSerializer(many=True)
