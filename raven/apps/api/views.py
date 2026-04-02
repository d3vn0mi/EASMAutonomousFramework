from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.clients.models import Asset, Client, Contact
from apps.engagements.models import Engagement, ScopeItem
from apps.findings.models import Finding
from apps.scanning.models import DiscoveredAsset, Scan
from apps.reports.models import Report
from .serializers import (
    AssetSerializer, ClientSerializer, ContactSerializer,
    EngagementSerializer, FindingSerializer, ScopeItemSerializer,
    ScanSerializer, DiscoveredAssetSerializer, ReportSerializer,
)


class IsAdminOrPM(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role in ("admin", "project_manager") or request.user.is_superuser


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPM]
    search_fields = ["name", "industry"]


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPM]

    def get_queryset(self):
        return Contact.objects.filter(client_id=self.kwargs["client_pk"])


class AssetViewSet(viewsets.ModelViewSet):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPM]

    def get_queryset(self):
        return Asset.objects.filter(client_id=self.kwargs["client_pk"])


class EngagementViewSet(viewsets.ModelViewSet):
    serializer_class = EngagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPM]
    filterset_fields = ["tier", "status", "client"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "tester":
            return user.assigned_engagements.all()
        return Engagement.objects.all()


class ScopeItemViewSet(viewsets.ModelViewSet):
    serializer_class = ScopeItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPM]

    def get_queryset(self):
        return ScopeItem.objects.filter(engagement_id=self.kwargs["engagement_pk"])


class FindingViewSet(viewsets.ModelViewSet):
    serializer_class = FindingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["severity", "remediation_status", "is_false_positive"]

    def get_queryset(self):
        return Finding.objects.filter(engagement_id=self.kwargs["engagement_pk"])


class ScanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Scan.objects.filter(engagement_id=self.kwargs["engagement_pk"])


class DiscoveredAssetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiscoveredAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DiscoveredAsset.objects.filter(engagement_id=self.kwargs["engagement_pk"])


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(engagement_id=self.kwargs["engagement_pk"])
