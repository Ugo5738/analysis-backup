from django.db import models

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


# === Floorplan Models ===


# Mimic floorplan/models.py: FloorPlanAnalysisResult
class FloorPlanAnalysisResult(TrackingModel):
    message = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    property_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} - {self.property_id}"


# Mimic FloorPlan model
class FloorPlan(TrackingModel):
    analysis_result = models.ForeignKey(
        FloorPlanAnalysisResult,
        related_name="backup_floor_plans",
        on_delete=models.CASCADE,
    )
    floorplan_id = models.CharField(max_length=255)
    original_url = models.URLField()

    def __str__(self):
        return self.floorplan_id


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

    def __str__(self):
        return f"Backup Dimensions for {self.room.room_name}"


# Mimic CsvRoomScalingFactors model
class CsvRoomScalingFactors(TrackingModel):
    csv_room = models.OneToOneField(
        CsvRoom, on_delete=models.CASCADE, related_name="backup_scaling_factors"
    )
    scale_metric = models.FloatField(null=True, blank=True)
    scale_imperial = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Backup Scaling Factors for {self.room.room_name}"


# To scale, remove bottle necks. E.g naming

# AllFloorsData
#      |
# CsvFloor
#      |
# CsvRoom
#      |
# [CsvRoomPixelData + CsvRoomDimensions + CsvRoomScalingFactors]

# future Ugo should be thanking past Ugo not being angry with past Ugo
# is future Ugo going to be thankful that I am making this decision
