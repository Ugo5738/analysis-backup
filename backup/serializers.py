from rest_framework import serializers

from backup.models import (
    BackupAnalysisTask,
    BackupProperty,
    BackupScrapingJob,
    BackupUser,
)


class BackupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupUser
        fields = ["id", "phone_number"]


class BackupPropertySerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True)
    user = BackupUserSerializer(read_only=True)

    class Meta:
        model = BackupProperty
        fields = "__all__"
        read_only_fields = ("updated_at",)

    def create(self, validated_data):
        phone = validated_data.pop("phone_number")
        backup_user, created = BackupUser.objects.get_or_create(phone_number=phone)
        validated_data["user"] = backup_user
        return BackupProperty.objects.create(**validated_data)


class BackupAnalysisTaskSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True)
    user = BackupUserSerializer(read_only=True)

    class Meta:
        model = BackupAnalysisTask
        fields = "__all__"
        read_only_fields = ("updated_at",)

    def create(self, validated_data):
        phone = validated_data.pop("phone_number")
        backup_user, created = BackupUser.objects.get_or_create(phone_number=phone)
        validated_data["user"] = backup_user
        return BackupAnalysisTask.objects.create(**validated_data)


class BackupScrapingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupScrapingJob
        fields = "__all__"
        read_only_fields = ("updated_at",)
