from rest_framework import serializers

from backup.models import BackupAnalysisTask, BackupProperty, BackupScrapingJob


class BackupPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupProperty
        fields = "__all__"
        read_only_fields = ("updated_at",)


class BackupAnalysisTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupAnalysisTask
        fields = "__all__"
        read_only_fields = ("updated_at",)


class BackupScrapingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupScrapingJob
        fields = "__all__"
        read_only_fields = ("updated_at",)
