import hashlib

from django.db import models
from simple_history.models import HistoricalRecords

from helpers.models import TrackingModel
from pabackup_service.config.logging_config import configure_logger

logger = configure_logger(__name__)

ANALYSIS_SOURCE = [("email", "Email"), ("original", "Original")]


class Property(models.Model):
    """
    Copy of a property record.
    """

    primary_key = models.IntegerField(unique=True)
    url = models.URLField()
    share_token = models.CharField(max_length=128, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    house_type = models.CharField(max_length=100, null=True, blank=True)
    agent = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    reviewed_description = models.TextField(null=True, blank=True)
    description_analysis = models.JSONField(null=True, blank=True)
    sentiment_analysis = models.JSONField(null=True, blank=True)
    listing_type = models.CharField(max_length=255, null=True, blank=True)
    time_on_market = models.CharField(max_length=255, null=True, blank=True)
    features = models.TextField(null=True, blank=True)
    floorplan_urls = models.JSONField(default=list, blank=True)
    overall_condition = models.JSONField(null=True, blank=True)
    detailed_analysis = models.JSONField(null=True, blank=True)
    failed_downloads = models.JSONField(default=list)
    image_urls = models.JSONField(default=list)
    overall_analysis = models.JSONField(null=True, blank=True)
    analysis_source = models.CharField(
        max_length=20, choices=ANALYSIS_SOURCE, default="original"
    )
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(table_name="history_sdb_properties")

    class Meta:
        db_table = "sdb_properties"
        verbose_name = "Property Data"
        verbose_name_plural = "Property Data Records"

    def __str__(self):
        return f"Property {self.primary_key} - {self.address or 'No Address'}"


class AnalysisTask(models.Model):
    primary_key = models.IntegerField(unique=True)
    property_primary_key = models.IntegerField()
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default="PENDING")
    progress = models.FloatField(default=0.0)
    stage = models.CharField(max_length=50, blank=True)
    stage_progress = models.JSONField(default=dict)
    trigger_analysis = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(table_name="history_sdb_analysis_tasks")

    class Meta:
        db_table = "sdb_analysis_tasks"
        verbose_name = "Analysis Task"
        verbose_name_plural = "Analysis Tasks"

    def __str__(self):
        return (
            f"Analysis Task {self.primary_key} for Property {self.property_primary_key}"
        )


class ScrapingJob(models.Model):
    primary_key = models.IntegerField(unique=True)
    url = models.URLField()
    source = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    callback_url = models.URLField(null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    property_id = models.IntegerField(null=True, blank=True)
    scraped_property_id = models.IntegerField(null=True, blank=True)
    task_id = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sdb_scraping_jobs"
        verbose_name = "Scraping Job"
        verbose_name_plural = "Scraping Jobs"


# === Floorplan Models ===


class FloorPlanAnalysisResult(TrackingModel):
    message = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    property_id = models.CharField(max_length=255)

    history = HistoricalRecords(table_name="history_sdb_fp_analysis_results")

    class Meta:
        db_table = "sdb_fp_analysis_results"
        unique_together = ("user_id", "property_id")
        indexes = [
            models.Index(fields=["user_id", "property_id"]),
        ]
        verbose_name = "Floor Plan Analysis Result"
        verbose_name_plural = "Floor Plan Analysis Results"

    def __str__(self):
        return f"Analysis: {self.user_id} - {self.property_id} (ID: {self.id})"


class FloorPlan(TrackingModel):
    analysis_result = models.ForeignKey(
        FloorPlanAnalysisResult,
        related_name="sdb_floor_plans",
        on_delete=models.CASCADE,
    )
    floorplan_id = models.CharField(
        max_length=64,
        db_index=True,  # unique=True,
    )  # Ensures DB-level uniqueness and speeds up lookups
    original_url = models.URLField(max_length=1024)
    update_count = models.PositiveIntegerField(
        default=0, help_text="Number of times webhook processing updated this record."
    )

    history = HistoricalRecords(table_name="history_sdb_floorplans")

    class Meta:
        db_table = "sdb_floorplans"
        unique_together = ("analysis_result", "floorplan_id")
        indexes = [
            models.Index(
                fields=["floorplan_id"]
            ),  # Can keep this index too if needed for other lookups
            # The unique_together constraint often implies an index anyway
        ]
        verbose_name = "Floor Plan"
        verbose_name_plural = "Floor Plans"

    def __str__(self):
        # Show first 8 chars of hash for brevity in admin dropdowns etc.
        short_hash = self.floorplan_id[:8] if self.floorplan_id else "N/A"
        return f"FP Hash: {short_hash}... (Analysis: {self.analysis_result_id})"

    @staticmethod
    def generate_hash_id(property_id, user_id, url):
        """
        Generates a SHA-256 hash for the combination of property ID, user ID,
        and URL string.
        """
        if not all([property_id, user_id, url]):  # Ensure all parts are non-empty
            raise ValueError(
                "Cannot generate hash: property_id, user_id, and url must all be provided and non-empty."
            )

        try:
            # Combine the strings with a separator unlikely to appear in the inputs
            combined_string = f"{property_id}|{user_id}|{url}"
            string_bytes = combined_string.encode("utf-8")
            return hashlib.sha256(string_bytes).hexdigest()
        except Exception as e:
            logger.error(
                f"Error generating combined hash for '{property_id}|{user_id}|{url}': {e}"
            )
            raise ValueError(f"Hashing failed for combined input") from e


class AllFloorsData(TrackingModel):
    floor_plan = models.OneToOneField(
        FloorPlan, related_name="sdb_all_floors_data", on_delete=models.CASCADE
    )
    json_file_url = models.URLField(max_length=1024, null=True, blank=True)
    csv_url = models.URLField(max_length=1024, null=True, blank=True)
    total_area_csv_url = models.URLField(max_length=1024, null=True, blank=True)
    image_labelme_side_by_side_url = models.URLField(
        max_length=1024, null=True, blank=True
    )
    notes = models.TextField(null=True, blank=True)

    history = HistoricalRecords(table_name="history_sdb_fp_all_floors_data")

    class Meta:
        db_table = "sdb_fp_all_floors_data"

    def __str__(self):
        fp_id = self.floor_plan.floorplan_id if self.floor_plan else "N/A"
        return f"All Floors Data for {fp_id}"


class PlanFloor(TrackingModel):
    floor_plan = models.ForeignKey(
        FloorPlan, related_name="sdb_plan_floors", on_delete=models.CASCADE
    )
    floor = models.CharField(max_length=255)  # e.g., "first_floor" or "ground_floor"
    label_me_url = models.URLField(max_length=1024, null=True, blank=True)
    json_file_url = models.URLField(max_length=1024, null=True, blank=True)
    image_url = models.URLField(max_length=1024, null=True, blank=True)
    labelme_image_url = models.URLField(max_length=1024, null=True, blank=True)
    csv_url = models.URLField(max_length=1024, null=True, blank=True)
    image_side_by_side_url = models.URLField(max_length=1024, null=True, blank=True)

    history = HistoricalRecords(table_name="history_sdb_fp_plan_floors")

    class Meta:
        db_table = "sdb_fp_plan_floors"

    def __str__(self):
        fp_id = self.floor_plan.floorplan_id if self.floor_plan else "N/A"
        return f"{self.floor} - {fp_id}"


class CsvFloor(TrackingModel):  # AllFloorsCsvfloor
    all_floors_data = models.ForeignKey(
        AllFloorsData, related_name="sdb_csv_floors", on_delete=models.CASCADE
    )
    floor_name = models.CharField(max_length=100, null=True, blank=True)
    calculated_total_area_metric = models.FloatField(null=True, blank=True)
    calculated_total_area_imperial = models.FloatField(null=True, blank=True)

    history = HistoricalRecords(table_name="history_sdb_fp_csv_floors")

    class Meta:
        db_table = "sdb_fp_csv_floors"

    def __str__(self):
        # Handle potential None for floor_name
        return self.floor_name or f"Unnamed Floor (ID: {self.id})"


# Mimic CsvRoom model
class CsvRoom(TrackingModel):
    csv_floor = models.ForeignKey(  # should be csv_floor
        CsvFloor, on_delete=models.CASCADE, related_name="sdb_rooms"
    )
    room_name = models.CharField(max_length=100, null=True, blank=True)
    is_segment = models.CharField(max_length=50, null=True, blank=True)
    room_id = models.FloatField(
        null=True, blank=True, db_index=True  # Index room_id within a floor
    )
    no_of_doors = models.FloatField(null=True, blank=True)
    no_of_windows = models.FloatField(null=True, blank=True)
    no_of_room_points = models.FloatField(null=True, blank=True)

    history = HistoricalRecords(table_name="history_sdb_fp_csv_rooms")

    class Meta:
        db_table = "sdb_fp_csv_rooms"

    def __str__(self):
        try:
            floor_name = self.csv_floor.floor_name or "Unnamed Floor"
        except CsvFloor.DoesNotExist:
            floor_name = "Detached Floor"
        room_name = self.room_name or f"Unnamed Room (ID: {self.id})"
        return f"{room_name} ({floor_name})"


class CsvRoomPixelData(TrackingModel):
    csv_room = models.OneToOneField(
        CsvRoom, on_delete=models.CASCADE, related_name="sdb_pixel_data"
    )
    # Numeric fields from CSV for pixel positions and areas:
    min_x_pixels = models.FloatField(null=True, blank=True)  # Min X Pixels
    min_y_pixels = models.FloatField(null=True, blank=True)  # Min Y Pixels
    max_x_pixels = models.FloatField(null=True, blank=True)  # Max X Pixels
    max_y_pixels = models.FloatField(null=True, blank=True)  # Max Y Pixels
    max_area_pixels = models.FloatField(null=True, blank=True)  # Max Area Pixels
    actual_area_pixels = models.FloatField(null=True, blank=True)  # Actual Area Pixels
    pixel_ratio = models.FloatField(null=True, blank=True)  # Pixel ratio

    history = HistoricalRecords(table_name="history_sdb_fp_csv_room_pixel_data")

    class Meta:
        db_table = "sdb_fp_csv_room_pixel_data"

    def __str__(self):
        try:
            room_name = self.csv_room.room_name or f"Unnamed Room (ID: {self.room.id})"
            return f"Pixel Data for {room_name}"
        except CsvRoom.DoesNotExist:
            return f"Pixel Data for Detached Room (ID: {self.id})"


class CsvRoomDimensions(TrackingModel):
    csv_room = models.OneToOneField(
        CsvRoom, on_delete=models.CASCADE, related_name="sdb_dimensions"
    )
    # Text fields for dimensions (Handles 'Unknown')
    dimensions_imperial = models.CharField(max_length=100, null=True, blank=True)
    dimensions_metric = models.CharField(max_length=100, null=True, blank=True)

    # Numeric fields for maximum areas
    max_area_metric = models.FloatField(null=True, blank=True)
    max_area_imperial = models.FloatField(null=True, blank=True)

    # Numeric fields for calculated areas:
    calculated_sq_area_metric = models.FloatField(null=True, blank=True)
    calculated_area_imperial = models.FloatField(null=True, blank=True)

    history = HistoricalRecords(table_name="history_sdb_fp_csv_room_dimensions")

    class Meta:
        db_table = "sdb_fp_csv_room_dimensions"

    def __str__(self):
        try:
            room_name = self.csv_room.room_name or f"Unnamed Room (ID: {self.room.id})"
            return f"Dimensions for {room_name}"
        except CsvRoom.DoesNotExist:
            return f"Dimensions for Detached Room (ID: {self.id})"


class CsvRoomScalingFactors(TrackingModel):
    csv_room = models.OneToOneField(
        CsvRoom, on_delete=models.CASCADE, related_name="sdb_scaling_factors"
    )
    scale_metric = models.FloatField(null=True, blank=True)
    scale_imperial = models.FloatField(null=True, blank=True)

    history = HistoricalRecords(table_name="history_sdb_fp_csv_room_scaling_factors")

    class Meta:
        db_table = "sdb_fp_csv_room_scaling_factors"

    def __str__(self):
        try:
            room_name = self.csv_room.room_name or f"Unnamed Room (ID: {self.room.id})"
            return f"Scaling Factors for {room_name}"
        except CsvRoom.DoesNotExist:
            return f"Scaling Factors for Detached Room (ID: {self.id})"


class AllFloorsCsvData(TrackingModel):
    """Stores a raw representation of a single row from all_floors.csv."""

    all_floors_data = models.ForeignKey(
        AllFloorsData,
        on_delete=models.CASCADE,
        related_name="all_floors_csv_data",
    )

    # --- Fields matching CSV columns ---
    # Object/String Columns
    floor_name = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    room_name = models.CharField(max_length=100, null=True, blank=True)
    is_segment = models.CharField(max_length=50, null=True, blank=True)
    dimensions_imperial = models.CharField(max_length=100, null=True, blank=True)
    dimensions_metric = models.CharField(max_length=100, null=True, blank=True)

    # Float64/Numeric Columns
    room_id = models.FloatField(null=True, blank=True, db_index=True)
    no_of_door = models.FloatField(null=True, blank=True)
    no_of_window = models.FloatField(null=True, blank=True)
    no_of_room_points = models.FloatField(null=True, blank=True)

    min_x_pixels = models.FloatField(
        null=True, blank=True, db_column="min_x_pixels_csv"
    )  # Use db_column if name conflicts/desired
    min_y_pixels = models.FloatField(
        null=True, blank=True, db_column="min_y_pixels_csv"
    )
    max_x_pixels = models.FloatField(
        null=True, blank=True, db_column="max_x_pixels_csv"
    )
    max_y_pixels = models.FloatField(
        null=True, blank=True, db_column="max_y_pixels_csv"
    )
    max_area_metric = models.FloatField(
        null=True, blank=True, db_column="max_area_metric_csv"
    )
    max_area_imperial = models.FloatField(
        null=True, blank=True, db_column="max_area_imperial_csv"
    )
    max_area_pixels = models.FloatField(
        null=True, blank=True, db_column="max_area_pixels_csv"
    )
    actual_area_pixels = models.FloatField(
        null=True, blank=True, db_column="actual_area_pixels_csv"
    )
    pixel_ratio = models.FloatField(null=True, blank=True, db_column="pixel_ratio_csv")
    scale_metric = models.FloatField(
        null=True, blank=True, db_column="scale_metric_csv"
    )
    scale_imperial = models.FloatField(
        null=True, blank=True, db_column="scale_imperial_csv"
    )
    calculated_sq_area_metric = models.FloatField(
        null=True, blank=True, db_column="calculated_sq_area_metric_csv"
    )
    calculated_floor_total_sq_area_metric = models.FloatField(
        null=True, blank=True, db_column="calc_floor_total_metric_csv"
    )
    calculated_area_imperial = models.FloatField(
        null=True, blank=True, db_column="calculated_area_imperial_csv"
    )  # Note lowercase 'c'
    calculated_floor_total_sq_area_imperial = models.FloatField(
        null=True, blank=True, db_column="calc_floor_total_imperial_csv"
    )

    history = HistoricalRecords(table_name="history_sdb_all_floors_csv_data")

    class Meta:
        db_table = "sdb_all_floors_csv_data"
        verbose_name = "All Floors CSV Data"
        verbose_name_plural = "All Floors CSV Data"
        indexes = [
            models.Index(fields=["all_floors_data", "floor_name"]),
            models.Index(fields=["all_floors_data", "room_id"]),
        ]

    def __str__(self):
        afd_id = self.all_floors_data_id if self.all_floors_data_id else "N/A"
        return (
            f"Raw Row for AFD:{afd_id} - Floor:{self.floor_name} RoomID:{self.room_id}"
        )


class TotalAreasCsvData(TrackingModel):
    """Stores parsed data from the total_area.csv file."""

    all_floors_data = models.ForeignKey(
        AllFloorsData, related_name="total_areas_csv_data", on_delete=models.CASCADE
    )
    area_name = models.CharField(max_length=500, null=True, blank=True)
    square_meters = models.FloatField(null=True, blank=True)
    square_feet = models.FloatField(null=True, blank=True)
    total_floors = models.IntegerField(null=True, blank=True)
    total_named_rooms = models.IntegerField(null=True, blank=True)
    total_segments = models.IntegerField(null=True, blank=True)
    total_points = models.IntegerField(null=True, blank=True)
    total_objects = models.IntegerField(null=True, blank=True)
    total_door_objects = models.IntegerField(null=True, blank=True)
    total_window_objects = models.IntegerField(null=True, blank=True)
    total_stair_objects = models.IntegerField(null=True, blank=True)
    list_of_objects = models.TextField(null=True, blank=True)
    total_actual_pixels = models.FloatField(null=True, blank=True)
    metric_scale = models.FloatField(null=True, blank=True)
    imperial_scale = models.FloatField(null=True, blank=True)
    input_image_tokens = models.IntegerField(null=True, blank=True)
    input_text_tokens = models.IntegerField(null=True, blank=True)
    output_text_tokens = models.IntegerField(null=True, blank=True)

    history = HistoricalRecords(table_name="history_sdb_total_areas_csv_data")

    class Meta:
        db_table = "sdb_total_areas_csv_data"
        unique_together = ("all_floors_data", "area_name")
        verbose_name = "Total Area CSV Data"
        verbose_name_plural = "Total Area CSV Data"

    def __str__(self):
        afd_id = (
            self.all_floors_data.floor_plan.floorplan_id
            if self.all_floors_data and self.all_floors_data.floor_plan
            else "N/A"
        )
        return f"{self.area_name or 'Unnamed Area'} for FloorPlan: {afd_id}"
