from django.db import transaction
from rest_framework import serializers

from backup.models import (
    AllFloorsCsvRawRow,
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
    TotalAreaData,
)

# Use standard logging or your custom config
from pabackup_service.config.logging_config import configure_logger

logger = configure_logger(__name__)


# ––––––– Basic Serializers –––––––
# PropertySerializer, AnalysisTaskSerializer, ScrapingJobSerializer remain here...


class PropertySerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )


class AnalysisTaskSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = AnalysisTask
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )


class ScrapingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingJob
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )


# ––––––– Serializers for Nested Backup Data –––––––

# --- Leaf Node Serializers (Define these first) ---


class CsvRoomPixelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CsvRoomPixelData
        exclude = ("csv_room", "id", "created_at", "updated_at")


class CsvRoomDimensionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CsvRoomDimensions
        exclude = ("csv_room", "id", "created_at", "updated_at")


class CsvRoomScalingFactorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CsvRoomScalingFactors
        exclude = ("csv_room", "id", "created_at", "updated_at")


class AllFloorsCsvRawRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllFloorsCsvRawRow
        fields = [
            "floor_name",
            "room_name",
            "is_segment",
            "dimensions_imperial",
            "dimensions_metric",
            "room_id",
            "no_of_door",
            "no_of_window",
            "no_of_room_points",
            "min_x_pixels",
            "min_y_pixels",
            "max_x_pixels",
            "max_y_pixels",
            "max_area_metric",
            "max_area_imperial",
            "max_area_pixels",
            "actual_area_pixels",
            "pixel_ratio",
            "scale_metric",
            "scale_imperial",
            "calculated_sq_area_metric",
            "calculated_floor_total_sq_area_metric",
            "calculated_area_imperial",
            "calculated_floor_total_sq_area_imperial",
            # DO NOT include fields like '0', '1', '2' here unless intended
        ]


class TotalAreaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TotalAreaData
        exclude = ("all_floors_data", "id", "created_at", "updated_at")


# --- Serializers used DIRECTLY by CompleteBackupFloorPlanSerializer (Define Before It) ---
# Moved FloorPlanAnalysisResultSerializer UP
class FloorPlanAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorPlanAnalysisResult
        # Use exclude if TrackingModel adds fields you don't want serialized
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )  # If TrackingModel provides these


# Moved PlanFloorSerializer UP
class PlanFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFloor
        exclude = ("floor_plan", "id", "created_at", "updated_at")


# --- Intermediate Nested Serializers (Define Before AllFloorsDataSerializer) ---


class CsvRoomSerializer(serializers.ModelSerializer):
    backup_pixel_data = CsvRoomPixelDataSerializer(required=False, allow_null=True)
    backup_dimensions = CsvRoomDimensionsSerializer(required=False, allow_null=True)
    backup_scaling_factors = CsvRoomScalingFactorsSerializer(
        required=False, allow_null=True
    )

    class Meta:
        model = CsvRoom
        exclude = ("csv_floor", "id", "created_at", "updated_at")


class CsvFloorSerializer(serializers.ModelSerializer):
    backup_rooms = CsvRoomSerializer(many=True, required=False, default=[])

    class Meta:
        model = CsvFloor
        exclude = ("all_floors_data", "id", "created_at", "updated_at")


# --- AllFloorsDataSerializer (Define Before CompleteBackupFloorPlanSerializer) ---
class AllFloorsDataSerializer(serializers.ModelSerializer):
    # Nested serializers for write operations
    backup_csv_floors = CsvFloorSerializer(many=True, required=False, default=[])
    backup_all_floors_raw_rows = AllFloorsCsvRawRowSerializer(
        many=True, required=False, default=[]
    )
    backup_total_area_data = TotalAreaDataSerializer(
        many=True, required=False, default=[]
    )

    class Meta:
        model = AllFloorsData
        exclude = ("floor_plan", "id", "created_at", "updated_at")

    def create(self, validated_data):
        """Creates AllFloorsData and all its nested children."""
        # ... (create logic remains the same as before) ...
        backup_csv_floors_data = validated_data.pop("backup_csv_floors", [])
        backup_raw_rows_data = validated_data.pop("backup_all_floors_raw_rows", [])
        backup_total_area_data = validated_data.pop("backup_total_area_data", [])

        all_floors_data_instance = AllFloorsData.objects.create(**validated_data)
        logger.debug(
            f"Created AllFloorsData instance with ID: {all_floors_data_instance.id}"
        )

        # --- Create Nested CsvFloor -> CsvRoom -> Details ---
        for csv_floor_data in backup_csv_floors_data:
            backup_rooms_data = csv_floor_data.pop("backup_rooms", [])
            csv_floor_instance = CsvFloor.objects.create(
                all_floors_data=all_floors_data_instance, **csv_floor_data
            )
            logger.debug(
                f"  Created CsvFloor: {csv_floor_instance.floor_name} (ID: {csv_floor_instance.id})"
            )

            rooms_to_create = []
            pixel_data_to_create_map = {}
            dimensions_data_to_create_map = {}
            scaling_factors_to_create_map = {}

            for idx, room_data in enumerate(backup_rooms_data):
                pixel_data = room_data.pop("backup_pixel_data", None)
                dimensions_data = room_data.pop("backup_dimensions", None)
                scaling_factors_data = room_data.pop("backup_scaling_factors", None)

                room_instance = CsvRoom(csv_floor=csv_floor_instance, **room_data)
                rooms_to_create.append(room_instance)

                if pixel_data:
                    pixel_data_to_create_map[idx] = pixel_data
                if dimensions_data:
                    dimensions_data_to_create_map[idx] = dimensions_data
                if scaling_factors_data:
                    scaling_factors_to_create_map[idx] = scaling_factors_data

            if rooms_to_create:
                created_rooms = CsvRoom.objects.bulk_create(rooms_to_create)
                logger.debug(
                    f"    Bulk created {len(created_rooms)} CsvRooms for floor {csv_floor_instance.floor_name}"
                )

                pixel_bulk = []
                dimensions_bulk = []
                scaling_bulk = []
                for idx, created_room in enumerate(created_rooms):
                    if idx in pixel_data_to_create_map:
                        pixel_bulk.append(
                            CsvRoomPixelData(
                                csv_room=created_room, **pixel_data_to_create_map[idx]
                            )
                        )
                    if idx in dimensions_data_to_create_map:
                        dimensions_bulk.append(
                            CsvRoomDimensions(
                                csv_room=created_room,
                                **dimensions_data_to_create_map[idx],
                            )
                        )
                    if idx in scaling_factors_to_create_map:
                        scaling_bulk.append(
                            CsvRoomScalingFactors(
                                csv_room=created_room,
                                **scaling_factors_to_create_map[idx],
                            )
                        )

                if pixel_bulk:
                    CsvRoomPixelData.objects.bulk_create(pixel_bulk)
                if dimensions_bulk:
                    CsvRoomDimensions.objects.bulk_create(dimensions_bulk)
                if scaling_bulk:
                    CsvRoomScalingFactors.objects.bulk_create(scaling_bulk)
                logger.debug(
                    f"    Bulk created related data for {len(created_rooms)} rooms."
                )

        # --- Bulk Create AllFloorsCsvRawRow ---
        raw_rows_to_create = [
            AllFloorsCsvRawRow(all_floors_data=all_floors_data_instance, **raw_row_data)
            for raw_row_data in backup_raw_rows_data
        ]
        if raw_rows_to_create:
            AllFloorsCsvRawRow.objects.bulk_create(raw_rows_to_create)
            logger.debug(
                f"  Bulk created {len(raw_rows_to_create)} AllFloorsCsvRawRow instances."
            )

        # --- Create/Update TotalAreaData ---
        total_area_instances = []
        for ta_data in backup_total_area_data:
            ta_instance, created = TotalAreaData.objects.update_or_create(
                all_floors_data=all_floors_data_instance,
                area_name=ta_data.get("area_name"),
                defaults=ta_data,
            )
            total_area_instances.append(ta_instance)
        if total_area_instances:
            logger.debug(
                f"  Created/Updated {len(total_area_instances)} TotalAreaData instances."
            )

        return all_floors_data_instance


# ––––––– Top Level Serializer (Define Last, as it uses others) –––––––


class CompleteBackupFloorPlanSerializer(serializers.ModelSerializer):
    # Nested serializers required for processing the input payload
    analysis_result = FloorPlanAnalysisResultSerializer()
    backup_all_floors_data = AllFloorsDataSerializer(required=False, allow_null=True)
    backup_plan_floors = PlanFloorSerializer(many=True, required=False, default=[])

    class Meta:
        model = FloorPlan
        fields = [
            "analysis_result",
            "floorplan_id",
            "original_url",
            "backup_all_floors_data",
            "backup_plan_floors",
            "id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    @transaction.atomic
    def create(self, validated_data):
        """Handles creation or update of a FloorPlan backup and its entire nested structure."""
        # ... (create logic remains the same as before) ...
        analysis_result_data = validated_data.pop("analysis_result")
        backup_all_floors_data_payload = validated_data.pop(
            "backup_all_floors_data", None
        )
        backup_plan_floors_payload = validated_data.pop("backup_plan_floors", [])
        floorplan_lookup_id = validated_data.get("floorplan_id")
        logger.info(
            f"Processing backup create/update for floorplan_id: {floorplan_lookup_id}"
        )

        analysis_result_instance, created_ar = (
            FloorPlanAnalysisResult.objects.update_or_create(
                user_id=analysis_result_data.get("user_id"),
                property_id=analysis_result_data.get("property_id"),
                defaults={"message": analysis_result_data.get("message")},
            )
        )
        logger.debug(
            f"{'Created' if created_ar else 'Found'} FloorPlanAnalysisResult ID: {analysis_result_instance.id}"
        )

        floorplan_instance, created_fp = FloorPlan.objects.update_or_create(
            analysis_result=analysis_result_instance,
            floorplan_id=floorplan_lookup_id,
            defaults={"original_url": validated_data.get("original_url")},
        )
        logger.debug(
            f"{'Created' if created_fp else 'Found'} FloorPlan ID: {floorplan_instance.id} (Floorplan_id field: {floorplan_lookup_id})"
        )

        if not created_fp:
            logger.info(
                f"Updating existing FloorPlan {floorplan_lookup_id}. Deleting old nested data..."
            )
            try:
                if (
                    hasattr(floorplan_instance, "backup_all_floors_data")
                    and floorplan_instance.backup_all_floors_data
                ):
                    logger.debug(
                        f"Deleting existing AllFloorsData ID: {floorplan_instance.backup_all_floors_data.id}"
                    )
                    floorplan_instance.backup_all_floors_data.delete()
            except AllFloorsData.DoesNotExist:
                logger.debug("No existing AllFloorsData found to delete.")

            deleted_pf_count, _ = floorplan_instance.backup_plan_floors.all().delete()
            logger.debug(f"Deleted {deleted_pf_count} existing PlanFloor instances.")
            logger.info(
                f"Finished deleting old nested data for FloorPlan {floorplan_lookup_id}."
            )

        if backup_all_floors_data_payload:
            logger.debug(
                f"Creating new AllFloorsData structure for FloorPlan {floorplan_lookup_id}..."
            )
            all_floors_serializer = AllFloorsDataSerializer(
                data=backup_all_floors_data_payload
            )
            all_floors_serializer.is_valid(raise_exception=True)
            all_floors_serializer.save(floor_plan=floorplan_instance)
            logger.debug(f"Successfully created new AllFloorsData structure.")
        else:
            logger.debug(
                "No 'backup_all_floors_data' provided in payload, skipping creation."
            )

        if backup_plan_floors_payload:
            logger.debug(
                f"Creating {len(backup_plan_floors_payload)} new PlanFloor instances..."
            )
            plan_floors_to_create = [
                PlanFloor(floor_plan=floorplan_instance, **pf_data)
                for pf_data in backup_plan_floors_payload
            ]
            if plan_floors_to_create:
                PlanFloor.objects.bulk_create(plan_floors_to_create)
                logger.debug(
                    f"Bulk created {len(plan_floors_to_create)} PlanFloor instances."
                )
        else:
            logger.debug(
                "No 'backup_plan_floors' provided in payload, skipping creation."
            )

        logger.info(
            f"Finished processing backup for floorplan_id: {floorplan_lookup_id}"
        )
        return floorplan_instance

    def update(self, instance, validated_data):
        logger.warning(
            "Direct call to CompleteBackupFloorPlanSerializer.update() is not the intended flow for create-or-replace logic."
        )
        raise NotImplementedError(
            "Update logic is handled within the create method for create-or-replace behavior."
        )
