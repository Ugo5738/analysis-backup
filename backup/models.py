from django.db import models
from simple_history.models import HistoricalRecords

from helpers.models import TrackingModel

ANALYSIS_SOURCE = [("email", "Email"), ("original", "Original")]


class Property(models.Model):
    """
    Backup copy of a property record.
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

    history = HistoricalRecords()

    class Meta:
        # db_table = "properties"
        verbose_name = "Property Data"
        verbose_name_plural = "Property Data Records"

    def __str__(self):
        return f"Property {self.primary_key} - {self.address or 'No Address'}"

    updated_at = models.DateTimeField(auto_now=True)


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

    history = HistoricalRecords()

    class Meta:
        # db_table = "analysis_tasks"
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
        # db_table = "scraping_jobs"

        verbose_name = "Scraping Job"
        verbose_name_plural = "Scraping Jobs"


# === Floorplan Models ===


# Mimic floorplan/models.py: FloorPlanAnalysisResult
class FloorPlanAnalysisResult(TrackingModel):
    message = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    property_id = models.CharField(max_length=255)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_analysis_results"
        unique_together = ("user_id", "property_id")
        indexes = [
            models.Index(fields=["user_id", "property_id"]),
        ]
        verbose_name = "Floor Plan Analysis Result"
        verbose_name_plural = "Floor Plan Analysis Results"

    def __str__(self):
        return f"Analysis: {self.user_id} - {self.property_id} (ID: {self.id})"


# Mimic FloorPlan model
class FloorPlan(TrackingModel):
    analysis_result = models.ForeignKey(
        FloorPlanAnalysisResult,
        related_name="backup_floor_plans",
        on_delete=models.CASCADE,
    )
    floorplan_id = models.CharField(max_length=255)
    original_url = models.URLField()

    history = HistoricalRecords()

    class Meta:
        # db_table = "floorplans"
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
        return f"FloorPlan: {self.floorplan_id} (AnalysisID: {self.analysis_result_id})"


# Mimic AllFloorsData model
class AllFloorsData(TrackingModel):
    floor_plan = models.OneToOneField(
        FloorPlan, related_name="backup_all_floors_data", on_delete=models.CASCADE
    )
    json_file_url = models.URLField()
    csv_url = models.URLField()  # change to all_floors_csv_url
    total_area_csv_url = models.URLField()
    image_labelme_side_by_side_url = models.URLField()
    notes = models.TextField(blank=True, null=True)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_all_floors_data"
        pass

    def __str__(self):
        return f"Backup All Floors Data for {self.floor_plan.floorplan_id}"


# Mimic PlanFloor model
class PlanFloor(TrackingModel):
    floor_plan = models.ForeignKey(
        FloorPlan, related_name="backup_plan_floors", on_delete=models.CASCADE
    )
    floor = models.CharField(max_length=255)
    label_me_url = models.URLField()
    json_file_url = models.URLField()
    image_url = models.URLField()
    labelme_image_url = models.URLField()
    csv_url = models.URLField()
    image_side_by_side_url = models.URLField()

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_plan_floors"
        pass

    def __str__(self):
        return f"{self.floor} - {self.floor_plan.floorplan_id}"


# Mimic CsvFloor model
class CsvFloor(TrackingModel):  # AllFloorsCsvfloor
    all_floors_data = models.ForeignKey(
        AllFloorsData, related_name="backup_csv_floors", on_delete=models.CASCADE
    )
    floor_name = models.CharField(max_length=100, null=True, blank=True)
    calculated_total_area_metric = models.FloatField(null=True, blank=True)
    calculated_total_area_imperial = models.FloatField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_csv_floors"
        pass

    def __str__(self):
        return self.floor_name


# Mimic CsvRoom model
class CsvRoom(TrackingModel):
    csv_floor = models.ForeignKey(  # should be csv_floor
        CsvFloor, on_delete=models.CASCADE, related_name="backup_rooms"
    )
    room_name = models.CharField(max_length=100, null=True, blank=True)
    is_segment = models.CharField(max_length=50, null=True, blank=True)
    room_id = models.FloatField(null=True, blank=True)
    no_of_doors = models.FloatField(null=True, blank=True)
    no_of_windows = models.FloatField(null=True, blank=True)
    no_of_room_points = models.FloatField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_csv_room_pixel_data"
        pass

    def __str__(self):
        return f"{self.room_name} ({self.floor.floor_name})"


# Mimic CsvRoomPixelData model
class CsvRoomPixelData(TrackingModel):
    csv_room = models.OneToOneField(
        CsvRoom, on_delete=models.CASCADE, related_name="backup_pixel_data"
    )
    min_x_pixels = models.FloatField(null=True, blank=True)
    min_y_pixels = models.FloatField(null=True, blank=True)
    max_x_pixels = models.FloatField(null=True, blank=True)
    max_y_pixels = models.FloatField(null=True, blank=True)
    max_area_pixels = models.FloatField(null=True, blank=True)
    actual_area_pixels = models.FloatField(null=True, blank=True)
    pixel_ratio = models.FloatField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_csv_room_dimensions"
        pass

    def __str__(self):
        return f"Backup Pixel Data for {self.room.room_name}"


# Mimic CsvRoomDimensions model
class CsvRoomDimensions(TrackingModel):
    csv_room = models.OneToOneField(
        CsvRoom, on_delete=models.CASCADE, related_name="backup_dimensions"
    )
    dimensions_imperial = models.CharField(max_length=100, null=True, blank=True)
    dimensions_metric = models.CharField(max_length=100, null=True, blank=True)
    max_area_metric = models.FloatField(null=True, blank=True)
    max_area_imperial = models.FloatField(null=True, blank=True)
    calculated_sq_area_metric = models.FloatField(null=True, blank=True)
    calculated_floor_total_sq_area_metric = models.FloatField(null=True, blank=True)
    calculated_area_imperial = models.FloatField(null=True, blank=True)
    calculated_floor_total_sq_area_imperial = models.FloatField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_csv_room_dimensions"
        pass

    def __str__(self):
        return f"Backup Dimensions for {self.room.room_name}"


# Mimic CsvRoomScalingFactors model
class CsvRoomScalingFactors(TrackingModel):
    csv_room = models.OneToOneField(
        CsvRoom, on_delete=models.CASCADE, related_name="backup_scaling_factors"
    )
    scale_metric = models.FloatField(null=True, blank=True)
    scale_imperial = models.FloatField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_csv_room_scaling_factors"
        pass

    def __str__(self):
        return f"Backup Scaling Factors for {self.room.room_name}"


# Mimic AllFloorsCsvRawRow model
class AllFloorsCsvRawRow(TrackingModel):
    """Stores a raw representation of a single row from all_floors.csv."""

    all_floors_data = models.ForeignKey(
        AllFloorsData,
        on_delete=models.CASCADE,
        related_name="backup_all_floors_raw_rows",
    )
    # Match fields from floorplan service's AllFloorsCsvRawRow model
    floor_name = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    room_name = models.CharField(max_length=100, null=True, blank=True)
    is_segment = models.CharField(max_length=50, null=True, blank=True)
    dimensions_imperial = models.CharField(max_length=100, null=True, blank=True)
    dimensions_metric = models.CharField(max_length=100, null=True, blank=True)
    room_id = models.FloatField(null=True, blank=True, db_index=True)
    no_of_door = models.FloatField(null=True, blank=True)
    no_of_window = models.FloatField(null=True, blank=True)
    no_of_room_points = models.FloatField(null=True, blank=True)
    min_x_pixels = models.FloatField(null=True, blank=True)
    min_y_pixels = models.FloatField(null=True, blank=True)
    max_x_pixels = models.FloatField(null=True, blank=True)
    max_y_pixels = models.FloatField(null=True, blank=True)
    max_area_metric = models.FloatField(null=True, blank=True)
    max_area_imperial = models.FloatField(null=True, blank=True)
    max_area_pixels = models.FloatField(null=True, blank=True)
    actual_area_pixels = models.FloatField(null=True, blank=True)
    pixel_ratio = models.FloatField(null=True, blank=True)
    scale_metric = models.FloatField(null=True, blank=True)
    scale_imperial = models.FloatField(null=True, blank=True)
    calculated_sq_area_metric = models.FloatField(null=True, blank=True)
    calculated_floor_total_sq_area_metric = models.FloatField(null=True, blank=True)
    calculated_area_imperial = models.FloatField(null=True, blank=True)
    calculated_floor_total_sq_area_imperial = models.FloatField(null=True, blank=True)
    # Add other fields if they exist in the source model/CSV (e.g., the numbered columns)

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_all_floors_raw_rows"
        verbose_name = "All Floors CSV Raw Row"
        verbose_name_plural = "All Floors CSV Raw Rows"
        indexes = [
            models.Index(fields=["all_floors_data", "floor_name"]),
            models.Index(fields=["all_floors_data", "room_id"]),
        ]

    def __str__(self):
        afd_id = self.all_floors_data_id if self.all_floors_data_id else "N/A"
        return (
            f"Raw Row for AFD:{afd_id} - Floor:{self.floor_name} RoomID:{self.room_id}"
        )


# Mimic TotalAreaData model
class TotalAreaData(TrackingModel):
    """Stores parsed data from the total_area.csv file (backup)."""

    all_floors_data = models.ForeignKey(
        AllFloorsData, related_name="backup_total_area_data", on_delete=models.CASCADE
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

    history = HistoricalRecords()

    class Meta:
        # db_table = "fp_total_area_data"
        unique_together = ("all_floors_data", "area_name")
        verbose_name = "Total Area Data"
        verbose_name_plural = "Total Area Data"

    def __str__(self):
        afd_id = (
            self.all_floors_data.floor_plan.floorplan_id
            if self.all_floors_data and self.all_floors_data.floor_plan
            else "N/A"
        )
        return f"{self.area_name or 'Unnamed Area'} for FloorPlan: {afd_id}"
