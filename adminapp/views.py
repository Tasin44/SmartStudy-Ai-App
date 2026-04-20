from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from coreapp.mixins import StandardResponseMixin, extract_first_error
from coreapp.paginations import StandardPagination
from profileapp.models import UserProfile
from scanapp.models import ScanHistory

from .models import TermsConditionSection
from .serializers import (
    AdminPasswordResetSerializer,
    AdminSelfUpdateSerializer,
    AdminUserCreateSerializer,
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    TermsConditionBulkCreateSerializer,
    TermsConditionSectionSerializer,
    get_current_plan_from_subscription,
    get_user_subscription_status,
    normalize_subscription_status,
)

User = get_user_model()


class AdminDashboardSummaryView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()

        # Placeholder until subscription module is integrated.
        subscribed_users = total_users

        return self.success_response(
            {
                "total_users": total_users,
                "subscribed_users": subscribed_users,
                "subscription_note": "Placeholder values (monthly/yearly) are being used for all users.",
            },
            message="Admin dashboard summary fetched successfully.",
        )


class AdminUserListCreateView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        queryset = User.objects.all().select_related("profile").order_by("-created_at")

        search = request.query_params.get("search")
        if search:
            search = search.strip()
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(profile__name__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        account_status = request.query_params.get("account_status")
        if account_status:
            normalized_account_status = account_status.strip().lower()
            if normalized_account_status in {"verified", "true", "1"}:
                queryset = queryset.filter(verified=True)
            elif normalized_account_status in {"not_verified", "unverified", "false", "0"}:
                queryset = queryset.filter(verified=False)
            else:
                return self.error_response(
                    "Invalid account_status. Use verified or not_verified.",
                    status_code=400,
                )

        subscription_status_filter = request.query_params.get("subscription_status")
        normalized_subscription_status = None
        if subscription_status_filter:
            raw_status = subscription_status_filter.strip().lower()
            if raw_status not in {"monthly", "yearly"}:
                return self.error_response(
                    "Invalid subscription_status. Use monthly or yearly.",
                    status_code=400,
                )
            normalized_subscription_status = normalize_subscription_status(raw_status)

        current_plan_filter = request.query_params.get("current_plan")
        normalized_current_plan = None
        if current_plan_filter:
            raw_plan = current_plan_filter.strip().lower()
            if raw_plan not in {"basic", "premium"}:
                return self.error_response(
                    "Invalid current_plan. Use basic or premium.",
                    status_code=400,
                )
            normalized_current_plan = raw_plan

        filtered_users = list(queryset)
        if normalized_subscription_status:
            filtered_users = [
                user
                for user in filtered_users
                if get_user_subscription_status(user) == normalized_subscription_status
            ]

        if normalized_current_plan:
            filtered_users = [
                user
                for user in filtered_users
                if get_current_plan_from_subscription(get_user_subscription_status(user)) == normalized_current_plan
            ]

        default_start_date = timezone.now().date()
        default_expiry_date = default_start_date + timedelta(days=30)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(filtered_users, request)
        serializer = AdminUserListSerializer(
            page,
            many=True,
            context={
                "request": request,
                "default_start_date": default_start_date,
                "default_expiry_date": default_expiry_date,
            },
        )

        paginated = paginator.get_paginated_response(serializer.data)
        return self.success_response(
            paginated.data,
            message="Users fetched successfully.",
        )

    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Failed to create user: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        user = serializer.save()
        payload = AdminUserListSerializer(user, context={"request": request}).data
        return self.success_response(payload, message="User created successfully.", status_code=201)


class AdminUserDetailView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, user_id):
        user = get_object_or_404(User.objects.select_related("profile"), id=user_id)
        serializer = AdminUserListSerializer(user, context={"request": request})
        return self.success_response(serializer.data, message="User details fetched successfully.")

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Failed to update user: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        serializer.update(user, serializer.validated_data)
        payload = AdminUserListSerializer(user, context={"request": request}).data
        return self.success_response(payload, message="User updated successfully.")


class AdminUserSubscriptionStatusView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("-created_at")
        default_start_date = timezone.now().date()
        default_expiry_date = default_start_date + timedelta(days=30)

        data = AdminUserListSerializer(
            users,
            many=True,
            context={
                "request": request,
                "default_start_date": default_start_date,
                "default_expiry_date": default_expiry_date,
            },
        ).data
        return self.success_response(data, message="Subscription status fetched successfully.")


class PopularSubjectsView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        popular_subjects = list(
            ScanHistory.objects.values("subject")
            .annotate(scan_count=Count("id"))
            .order_by("-scan_count", "subject")
        )

        return self.success_response(
            {
                "popular_subjects": popular_subjects,
            },
            message="Popular subjects fetched successfully.",
        )


class ActiveUsersAnalyticsView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        start_7_days = today - timedelta(days=6)
        start_30_days = today - timedelta(days=29)

        today_active_users = (
            ScanHistory.objects.filter(created_at__date=today)
            .values("user")
            .distinct()
            .count()
        )
        last_7_days_active_users = (
            ScanHistory.objects.filter(created_at__date__range=[start_7_days, today])
            .values("user")
            .distinct()
            .count()
        )
        last_30_days_active_users = (
            ScanHistory.objects.filter(created_at__date__range=[start_30_days, today])
            .values("user")
            .distinct()
            .count()
        )

        daily_data = (
            ScanHistory.objects.filter(created_at__date__range=[start_30_days, today])
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(active_users=Count("user", distinct=True))
            .order_by("day")
        )

        return self.success_response(
            {
                "today_active_users": today_active_users,
                "last_7_days_active_users": last_7_days_active_users,
                "last_30_days_active_users": last_30_days_active_users,
                "daily_breakdown": list(daily_data),
            },
            message="Active users analytics fetched successfully.",
        )


class AdminSelfProfileView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        image = None
        if profile.image:
            image = request.build_absolute_uri(profile.image.url)

        data = {
            "id": request.user.id,
            "name": profile.name or request.user.username,
            "image": image,
            "email": request.user.email,
        }
        return self.success_response(data, message="Admin profile fetched successfully.")

    def patch(self, request):
        serializer = AdminSelfUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Failed to update admin profile: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if "name" in serializer.validated_data:
            profile.name = serializer.validated_data["name"]
        if "image" in serializer.validated_data:
            profile.image = serializer.validated_data["image"]
        profile.save()

        if "email" in serializer.validated_data:
            new_email = serializer.validated_data["email"].strip().lower()
            if User.objects.exclude(id=request.user.id).filter(email=new_email).exists():
                return self.error_response(
                    "Failed to update admin profile: This email is already in use.",
                    status_code=400,
                )

            request.user.email = new_email
            request.user.username = new_email
            request.user.save(update_fields=["email", "username", "updated_at"])

        image = None
        if profile.image:
            image = request.build_absolute_uri(profile.image.url)

        data = {
            "id": request.user.id,
            "name": profile.name or request.user.username,
            "image": image,
            "email": request.user.email,
        }
        return self.success_response(data, message="Admin profile updated successfully.")


class AdminResetPasswordView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = AdminPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Failed to reset password: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        old_password = serializer.validated_data["old_password"]
        if not request.user.check_password(old_password):
            return self.error_response(
                "Failed to reset password: Old password is incorrect.",
                status_code=400,
            )

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])
        return self.success_response({}, message="Admin password reset successfully.")


class TermsConditionSectionsView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [JSONParser]

    def get(self, request):
        sections = TermsConditionSection.objects.all().order_by("order", "created_at")
        serialized = TermsConditionSectionSerializer(sections, many=True)
        return self.success_response(serialized.data, message="Terms sections fetched successfully.")

    def post(self, request):
        serializer = TermsConditionBulkCreateSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Failed to create terms sections: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        created = []
        for section in serializer.validated_data["sections"]:
            created.append(
                TermsConditionSection.objects.create(
                    section_name=section["section_name"],
                    description=section["description"],
                    order=section.get("order", 0),
                    created_by=request.user,
                )
            )

        payload = TermsConditionSectionSerializer(created, many=True).data
        return self.success_response(payload, message="Terms sections created successfully.", status_code=201)


class TermsConditionSectionDetailView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [JSONParser]

    def patch(self, request, section_id):
        section = get_object_or_404(TermsConditionSection, id=section_id)
        serializer = TermsConditionSectionSerializer(section, data=request.data, partial=True)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(
                f"Failed to update terms section: {reason}",
                status_code=400,
                data=serializer.errors,
            )

        serializer.save()
        return self.success_response(serializer.data, message="Terms section updated successfully.")

    def delete(self, request, section_id):
        section = get_object_or_404(TermsConditionSection, id=section_id)
        section.delete()
        return self.success_response({}, message="Terms section deleted successfully.")


class TermsConditionSummaryView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        sections = TermsConditionSection.objects.all().order_by("order", "created_at")
        serialized = TermsConditionSectionSerializer(sections, many=True).data

        full_text = "\n\n".join(
            [f"{item['section_name']}\n{item['description']}" for item in serialized]
        ).strip()

        total_words = len(full_text.split()) if full_text else 0

        return self.success_response(
            {
                "total_sections": len(serialized),
                "total_words": total_words,
                "terms_and_conditions": serialized,
                "whole_terms_text": full_text,
            },
            message="Terms and conditions summary fetched successfully.",
        )
