from rest_framework import serializers
from apps.clients.models import Asset, Client, CompanyProfile, Contact
from apps.engagements.models import Engagement, ScopeItem
from apps.findings.models import BreachRecord, Finding
from apps.scanning.models import DiscoveredAsset, Scan
from apps.correlation.models import CorrelationResult
from apps.reports.models import Report


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = "__all__"


class EngagementSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = Engagement
        fields = "__all__"


class ScopeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScopeItem
        fields = "__all__"


class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = "__all__"


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = "__all__"


class DiscoveredAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoveredAsset
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = "__all__"


class BreachRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreachRecord
        fields = "__all__"


class CorrelationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrelationResult
        fields = "__all__"
