

from django.urls import path
from .views import ScanView,ScanHistoryView

urlpatterns = [
    path('',ScanView.as_view(),name='scan'),
    path('history/',ScanHistoryView.as_view(),name='scan-history'),#❓❓❓how does this name impact
    
]

















