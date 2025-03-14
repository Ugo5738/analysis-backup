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


# ––––––– Analysis Result and FloorPlan Serializers –––––––
class BackupFloorPlanAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupFloorPlanAnalysisResult
        fields = "__all__"


class BackupFloorPlanSerializer(serializers.ModelSerializer):
    analysis_result = BackupFloorPlanAnalysisResultSerializer()

    class Meta:
        model = BackupFloorPlan
        fields = "__all__"

    def create(self, validated_data):
        analysis_result_data = validated_data.pop("analysis_result")
        analysis_result = BackupFloorPlanAnalysisResult.objects.create(
            **analysis_result_data
        )
        backup_floorplan = BackupFloorPlan.objects.create(
            analysis_result=analysis_result, **validated_data
        )
        return backup_floorplan


# ––––––– Nested All Floors Data (including CSV floors/rooms) –––––––
class BackupAllFloorsDataSerializer(serializers.ModelSerializer):
    # Include nested CSV floors data via a raw list (you can later enhance this with a nested serializer)
    backup_csv_floors = serializers.ListField(
        child=serializers.DictField(), required=False
    )

    class Meta:
        model = BackupAllFloorsData
        fields = "__all__"

    def create(self, validated_data):
        csv_floors_data = validated_data.pop("backup_csv_floors", [])
        all_floors_data = BackupAllFloorsData.objects.create(**validated_data)
        for csv_floor_data in csv_floors_data:
            backup_rooms_data = csv_floor_data.pop("backup_rooms", [])
            csv_floor = BackupCsvFloor.objects.create(
                all_floors_data=all_floors_data, **csv_floor_data
            )
            for room_data in backup_rooms_data:
                # Extract and remove nested room data if available
                backup_pixel_data = room_data.pop("backup_pixel_data", None)
                backup_dimensions = room_data.pop("backup_dimensions", None)
                backup_scaling_factors = room_data.pop("backup_scaling_factors", None)
                room = BackupCsvRoom.objects.create(floor=csv_floor, **room_data)
                if backup_pixel_data:
                    BackupCsvRoomPixelData.objects.create(
                        room=room, **backup_pixel_data
                    )
                if backup_dimensions:
                    BackupCsvRoomDimensions.objects.create(
                        room=room, **backup_dimensions
                    )
                if backup_scaling_factors:
                    BackupCsvRoomScalingFactors.objects.create(
                        room=room, **backup_scaling_factors
                    )
        return all_floors_data


# ––––––– Plan Floor Serializer –––––––
class BackupPlanFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupPlanFloor
        fields = "__all__"


# ––––––– Complete FloorPlan Backup Serializer –––––––
class CompleteBackupFloorPlanSerializer(serializers.ModelSerializer):
    analysis_result = BackupFloorPlanAnalysisResultSerializer()
    backup_all_floors_data = BackupAllFloorsDataSerializer(required=False)
    backup_plan_floors = BackupPlanFloorSerializer(many=True, required=False)

    class Meta:
        model = BackupFloorPlan
        fields = "__all__"

    def create(self, validated_data):
        analysis_result_data = validated_data.pop("analysis_result")
        backup_all_floors_data_data = validated_data.pop("backup_all_floors_data", None)
        backup_plan_floors_data = validated_data.pop("backup_plan_floors", [])

        # Create the analysis result and floorplan
        analysis_result = BackupFloorPlanAnalysisResult.objects.create(
            **analysis_result_data
        )
        backup_floorplan = BackupFloorPlan.objects.create(
            analysis_result=analysis_result, **validated_data
        )

        # Create the all floors data (with nested CSV floors/rooms) if provided
        if backup_all_floors_data_data:
            backup_all_floors_data_data["floor_plan"] = backup_floorplan
            serializer = BackupAllFloorsDataSerializer(data=backup_all_floors_data_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        # Create plan floors
        for plan_floor_data in backup_plan_floors_data:
            plan_floor_data["floor_plan"] = backup_floorplan
            BackupPlanFloor.objects.create(**plan_floor_data)

        return backup_floorplan
