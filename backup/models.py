from django.db import models

from helpers.models import TrackingModel

ANALYSIS_SOURCE = [("email", "Email"), ("original", "Original")]


class BackupUser(TrackingModel):
    """
    A simplified user model for the backup service that stores only the unique phone number
    (plus timestamps) to track which user analyzed a property.
    """

    phone_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_number


class BackupProperty(models.Model):
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

    # Association to a backup-specific user (optional at first)
    user = models.ForeignKey(
        BackupUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="properties",
    )

    def __str__(self):
        return f"Property {self.primary_key} - {self.address or 'No Address'}"

    updated_at = models.DateTimeField(auto_now=True)


class BackupAnalysisTask(models.Model):
    primary_key = models.IntegerField(unique=True)
    property_primary_key = models.IntegerField()
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default="PENDING")
    progress = models.FloatField(default=0.0)
    stage = models.CharField(max_length=50, blank=True)
    stage_progress = models.JSONField(default=dict)
    trigger_analysis = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Association to a backup-specific user (optional)
    user = models.ForeignKey(
        BackupUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analysis_tasks",
    )

    def __str__(self):
        return (
            f"Analysis Task {self.primary_key} for Property {self.property_primary_key}"
        )


class BackupScrapingJob(models.Model):
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
