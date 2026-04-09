# -*- coding: utf-8 -*-
"""
URLs de l'API REST Super Admin.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.superadmin.api.viewsets import (
    MetricsViewSet,
    GeoViewSet,
    MembershipProfileViewSet,
    EventPassViewSet,
    TransformationViewSet,
    SystemControlViewSet,
    AlertsViewSet,
)

router = DefaultRouter()
router.register(r'metrics', MetricsViewSet, basename='metrics')
router.register(r'geo', GeoViewSet, basename='geo')
router.register(r'memberships', MembershipProfileViewSet, basename='memberships')
router.register(r'event-passes', EventPassViewSet, basename='event-passes')
router.register(r'transformations', TransformationViewSet, basename='transformations')
router.register(r'system', SystemControlViewSet, basename='system')
router.register(r'alerts', AlertsViewSet, basename='alerts')

urlpatterns = [
    path('', include(router.urls)),
]
