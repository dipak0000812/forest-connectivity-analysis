from django.urls import path, include
from src.forest_connectivity.api import ForestConnectivityView, ForestConnectivityDetailView

urlpatterns = [
    path('api/v1/forest-connectivity/', ForestConnectivityView.as_view(), name='forest-connectivity-list'),
    path('api/v1/forest-connectivity/<uuid:task_id>/', ForestConnectivityDetailView.as_view(), name='forest-connectivity-detail'),
    path('', include('django_prometheus.urls')),
]
