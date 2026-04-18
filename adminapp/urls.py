from django.urls import path

from .views import (
    ActiveUsersAnalyticsView,
    AdminDashboardSummaryView,
    AdminResetPasswordView,
    AdminSelfProfileView,
    AdminUserDetailView,
    AdminUserListCreateView,
    AdminUserSubscriptionStatusView,
    PopularSubjectsView,
    TermsConditionSectionDetailView,
    TermsConditionSectionsView,
    TermsConditionSummaryView,
)

urlpatterns = [
    path("dashboard/", AdminDashboardSummaryView.as_view(), name="admin-dashboard-summary"),
    path("users/", AdminUserListCreateView.as_view(), name="admin-users"),
    path("users/<uuid:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path(
        "users/subscription-status/",
        AdminUserSubscriptionStatusView.as_view(),
        name="admin-user-subscription-status",
    ),
    path("analytics/popular-subjects/", PopularSubjectsView.as_view(), name="admin-popular-subjects"),
    path("analytics/active-users/", ActiveUsersAnalyticsView.as_view(), name="admin-active-users"),
    path("me/", AdminSelfProfileView.as_view(), name="admin-self-profile"),
    path("me/reset-password/", AdminResetPasswordView.as_view(), name="admin-reset-password"),
    path("terms/sections/", TermsConditionSectionsView.as_view(), name="admin-terms-sections"),
    path(
        "terms/sections/<uuid:section_id>/",
        TermsConditionSectionDetailView.as_view(),
        name="admin-terms-section-detail",
    ),
    path("terms/", TermsConditionSummaryView.as_view(), name="admin-terms-summary"),
]
