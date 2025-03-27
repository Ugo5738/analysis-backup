from rest_framework import serializers

from backup.models import (
    AllFloorsData,
    AnalysisTask,
    CsvFloor,
    CsvRoom,
    CsvRoomDimensions,
    CsvRoomPixelData,
    CsvRoomScalingFactors,
    FloorPlan,
    FloorPlanAnalysisResult,
    PlanFloor,
    Property,
    ScrapingJob,
)

# ––––––– Basic Serializers –––––––


class BackupPropertySerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = ("updated_at",)

    def create(self, validated_data):
        phone = validated_data.pop("phone_number")
        return Property.objects.create(**validated_data)


class BackupAnalysisTaskSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = AnalysisTask
        fields = "__all__"
        read_only_fields = ("updated_at",)

    def create(self, validated_data):
        phone = validated_data.pop("phone_number")
        return AnalysisTask.objects.create(**validated_data)


class BackupScrapingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingJob
        fields = "__all__"
        read_only_fields = ("updated_at",)


# ––––––– Nested CSV Data Serializers –––––––


class BackupCsvRoomPixelDataSerializer(serializers.ModelSerializer):
    # Mark 'room' as read-only so it isn’t required in the input.
    room = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CsvRoomPixelData
        fields = "__all__"


class BackupCsvRoomDimensionsSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CsvRoomDimensions
        fields = "__all__"


class BackupCsvRoomScalingFactorsSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CsvRoomScalingFactors
        fields = "__all__"


class BackupCsvRoomSerializer(serializers.ModelSerializer):
    # 'floor' will be set automatically during creation.
    floor = serializers.PrimaryKeyRelatedField(read_only=True)
    backup_pixel_data = BackupCsvRoomPixelDataSerializer(required=False)
    backup_dimensions = BackupCsvRoomDimensionsSerializer(required=False)
    backup_scaling_factors = BackupCsvRoomScalingFactorsSerializer(required=False)

    class Meta:
        model = CsvRoom
        fields = "__all__"


class BackupCsvFloorSerializer(serializers.ModelSerializer):
    # 'all_floors_data' is set by the parent so mark it as read-only.
    all_floors_data = serializers.PrimaryKeyRelatedField(read_only=True)

    # Use nested serializer for rooms.
    backup_rooms = BackupCsvRoomSerializer(many=True, required=False)

    class Meta:
        model = CsvFloor
        fields = "__all__"


# ––––––– Nested All Floors Data (including CSV floors/rooms) –––––––


class BackupAllFloorsDataSerializer(serializers.ModelSerializer):
    # Use the nested serializer with many=True
    backup_csv_floors = BackupCsvFloorSerializer(many=True, required=False)

    class Meta:
        model = AllFloorsData
        fields = "__all__"
        extra_kwargs = {
            "floor_plan": {"read_only": True},
        }

    def create(self, validated_data):
        csv_floors_data = validated_data.pop("backup_csv_floors", [])
        all_floors_data = AllFloorsData.objects.create(**validated_data)
        for csv_floor_data in csv_floors_data:
            backup_rooms_data = csv_floor_data.pop("backup_rooms", [])
            csv_floor = CsvFloor.objects.create(
                all_floors_data=all_floors_data, **csv_floor_data
            )
            for room_data in backup_rooms_data:
                # Extract and remove nested room data if available
                backup_pixel_data = room_data.pop("backup_pixel_data", None)
                backup_dimensions = room_data.pop("backup_dimensions", None)
                backup_scaling_factors = room_data.pop("backup_scaling_factors", None)
                room = CsvRoom.objects.create(floor=csv_floor, **room_data)
                if backup_pixel_data:
                    CsvRoomPixelData.objects.create(room=room, **backup_pixel_data)
                if backup_dimensions:
                    CsvRoomDimensions.objects.create(room=room, **backup_dimensions)
                if backup_scaling_factors:
                    CsvRoomScalingFactors.objects.create(
                        room=room, **backup_scaling_factors
                    )
        return all_floors_data


# ––––––– Analysis Result and FloorPlan Serializers –––––––
class BackupFloorPlanAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorPlanAnalysisResult
        fields = "__all__"


class BackupFloorPlanSerializer(serializers.ModelSerializer):
    analysis_result = BackupFloorPlanAnalysisResultSerializer()

    class Meta:
        model = FloorPlan
        fields = "__all__"

    def create(self, validated_data):
        analysis_result_data = validated_data.pop("analysis_result")
        analysis_result = FloorPlanAnalysisResult.objects.create(**analysis_result_data)
        backup_floorplan = FloorPlan.objects.create(
            analysis_result=analysis_result, **validated_data
        )
        return backup_floorplan


# ––––––– Plan Floor Serializer –––––––
class BackupPlanFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFloor
        fields = "__all__"
        extra_kwargs = {
            "floor_plan": {"read_only": True},  # Mark floor_plan as read-only
        }


# ––––––– Complete FloorPlan Backup Serializer –––––––
class CompleteBackupFloorPlanSerializer(serializers.ModelSerializer):
    analysis_result = BackupFloorPlanAnalysisResultSerializer()
    backup_all_floors_data = BackupAllFloorsDataSerializer(required=False)
    backup_plan_floors = BackupPlanFloorSerializer(many=True, required=False)

    class Meta:
        model = FloorPlan
        fields = "__all__"

    def create(self, validated_data):
        analysis_result_data = validated_data.pop("analysis_result")
        backup_all_floors_data_data = validated_data.pop("backup_all_floors_data", None)
        backup_plan_floors_data = validated_data.pop("backup_plan_floors", [])

        # Create the analysis result and backup floorplan
        analysis_result = FloorPlanAnalysisResult.objects.create(**analysis_result_data)
        backup_floorplan = FloorPlan.objects.create(
            analysis_result=analysis_result, **validated_data
        )

        # Create the all floors data with nested CSV floors/rooms if provided.
        if backup_all_floors_data_data:
            # Pass the backup_floorplan explicitly as floor_plan
            serializer = BackupAllFloorsDataSerializer(data=backup_all_floors_data_data)
            serializer.is_valid(raise_exception=True)
            serializer.save(floor_plan=backup_floorplan)

        # Create plan floors, explicitly assigning the floor_plan
        for plan_floor_data in backup_plan_floors_data:
            PlanFloor.objects.create(floor_plan=backup_floorplan, **plan_floor_data)

        return backup_floorplan
