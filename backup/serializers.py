from rest_framework import serializers

from backup.models import (
    BackupAllFloorsData,
    BackupAnalysisTask,
    BackupCsvFloor,
    BackupCsvRoom,
    BackupCsvRoomDimensions,
    BackupCsvRoomPixelData,
    BackupCsvRoomScalingFactors,
    BackupFloorPlan,
    BackupFloorPlanAnalysisResult,
    BackupPlanFloor,
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


class BackupFloorPlanAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupFloorPlanAnalysisResult
        fields = "__all__"


class BackupFloorPlanSerializer(serializers.ModelSerializer):
    analysis_result = BackupFloorPlanAnalysisResultSerializer()

    class Meta:
        model = BackupFloorPlan
        fields = "__all__"


class BackupAllFloorsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupAllFloorsData
        fields = "__all__"


class BackupPlanFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupPlanFloor
        fields = "__all__"


class BackupCsvRoomPixelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupCsvRoomPixelData
        fields = "__all__"


class BackupCsvRoomDimensionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupCsvRoomDimensions
        fields = "__all__"


class BackupCsvRoomScalingFactorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupCsvRoomScalingFactors
        fields = "__all__"


class BackupCsvRoomSerializer(serializers.ModelSerializer):
    backup_pixel_data = BackupCsvRoomPixelDataSerializer(required=False)
    backup_dimensions = BackupCsvRoomDimensionsSerializer(required=False)
    backup_scaling_factors = BackupCsvRoomScalingFactorsSerializer(required=False)

    class Meta:
        model = BackupCsvRoom
        fields = "__all__"


class BackupCsvFloorSerializer(serializers.ModelSerializer):
    backup_rooms = BackupCsvRoomSerializer(many=True, required=False)

    class Meta:
        model = BackupCsvFloor
        fields = "__all__"


# Finally, a serializer for the complete floorplan backup payload:
class CompleteBackupFloorPlanSerializer(serializers.ModelSerializer):
    backup_all_floors_data = BackupAllFloorsDataSerializer(required=False)
    backup_plan_floors = BackupPlanFloorSerializer(many=True, required=False)
    # You can nest additional serializers for CSV data if needed

    class Meta:
        model = BackupFloorPlan
        fields = "__all__"
