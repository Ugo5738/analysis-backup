from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.urls import reverse
from django.utils.html import format_html

from .models import BackupAnalysisTask, BackupProperty, BackupScrapingJob


class AnalysisSourceFilter(SimpleListFilter):
    title = "Analysis Source"
    parameter_name = "analysis_source"

    def lookups(self, request, model_admin):
        return [
            ("email", "Email"),
            ("original", "Original"),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(analysis_source=self.value())
        return queryset


class PropertyStatusFilter(SimpleListFilter):
    title = "Property Status"
    parameter_name = "property_status"

    def lookups(self, request, model_admin):
        return [
            ("with_analysis", "With Analysis"),
            ("no_analysis", "No Analysis"),
            ("with_images", "With Images"),
            ("no_images", "No Images"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "with_analysis":
            return queryset.exclude(overall_analysis__isnull=True)
        elif self.value() == "no_analysis":
            return queryset.filter(overall_analysis__isnull=True)
        elif self.value() == "with_images":
            return queryset.exclude(image_urls=[])
        elif self.value() == "no_images":
            return queryset.filter(image_urls=[])
        return queryset


@admin.register(BackupProperty)
class BackupPropertyAdmin(admin.ModelAdmin):
    list_display = (
        "primary_key",
        "address",
        "price_display",
        "bedrooms",
        "bathrooms",
        "house_type",
        "listing_type",
        "time_on_market",
        "analysis_source",
        "has_images",
        "has_analysis",
        "updated_at",
    )
    list_filter = (
        "house_type",
        "listing_type",
        AnalysisSourceFilter,
        PropertyStatusFilter,
        "updated_at",
    )
    search_fields = ("primary_key", "address", "agent", "description")
    readonly_fields = ("updated_at", "property_url", "image_preview")
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "primary_key",
                    "url",
                    "property_url",
                    "share_token",
                    "phone_number",
                    "address",
                )
            },
        ),
        (
            "Property Details",
            {
                "fields": (
                    "price",
                    "bedrooms",
                    "bathrooms",
                    "size",
                    "house_type",
                    "agent",
                    "listing_type",
                    "time_on_market",
                )
            },
        ),
        ("Description", {"fields": ("description", "reviewed_description")}),
        (
            "Features and Media",
            {
                "fields": (
                    "features",
                    "image_preview",
                    "image_urls",
                    "floorplan_urls",
                    "failed_downloads",
                )
            },
        ),
        (
            "Analysis",
            {
                "fields": (
                    "description_analysis",
                    "sentiment_analysis",
                    "overall_condition",
                    "detailed_analysis",
                    "overall_analysis",
                    "analysis_source",
                )
            },
        ),
        ("Metadata", {"fields": ("updated_at",)}),
    )

    def price_display(self, obj):
        if obj.price:
            return f"${obj.price:,.2f}"
        return "-"

    price_display.short_description = "Price"

    def has_images(self, obj):
        return bool(obj.image_urls)

    has_images.boolean = True
    has_images.short_description = "Has Images"

    def has_analysis(self, obj):
        return bool(obj.overall_analysis)

    has_analysis.boolean = True
    has_analysis.short_description = "Has Analysis"

    def property_url(self, obj):
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank">View Property</a>', obj.url
            )
        return "-"

    property_url.short_description = "Property Link"

    def image_preview(self, obj):
        if not obj.image_urls:
            return "No images available"

        html = (
            '<div style="display: flex; flex-wrap: wrap; gap: 10px; max-width: 800px;">'
        )
        for i, url in enumerate(obj.image_urls):
            if i < 5:  # Show first 5 images only
                html += f'<img src="{url}" style="width: 150px; height: auto; object-fit: cover;" />'

        if len(obj.image_urls) > 5:
            html += f'<div style="width: 150px; height: 150px; display: flex; align-items: center; justify-content: center; background-color: #f0f0f0;">+{len(obj.image_urls) - 5} more</div>'

        html += "</div>"
        return format_html(html)

    image_preview.short_description = "Image Preview"


class TaskStatusFilter(SimpleListFilter):
    title = "Task Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [
            ("PENDING", "Pending"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(BackupAnalysisTask)
class BackupAnalysisTaskAdmin(admin.ModelAdmin):
    list_display = (
        "primary_key",
        "property_link",
        "status",
        "progress_display",
        "stage",
        "trigger_analysis",
        "updated_at",
    )
    list_filter = (TaskStatusFilter, "trigger_analysis", "updated_at")
    search_fields = ("primary_key", "property_primary_key", "phone_number")
    readonly_fields = ("updated_at", "property_link", "progress_bar")
    fieldsets = (
        (
            "Task Information",
            {
                "fields": (
                    "primary_key",
                    "property_primary_key",
                    "property_link",
                    "phone_number",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "progress",
                    "progress_bar",
                    "stage",
                    "stage_progress",
                )
            },
        ),
        ("Options", {"fields": ("trigger_analysis",)}),
        ("Metadata", {"fields": ("updated_at",)}),
    )

    def progress_display(self, obj):
        return f"{obj.progress * 100:.1f}%"

    progress_display.short_description = "Progress"

    def progress_bar(self, obj):
        progress_percentage = int(obj.progress * 100)
        color = "#4CAF50" if progress_percentage == 100 else "#2196F3"
        return format_html(
            '<div style="width: 100%; background-color: #f0f0f0; border-radius: 5px;">'
            '<div style="height: 20px; width: {}%; background-color: {}; border-radius: 5px; text-align: center; color: white;">'
            "{:.1f}%</div></div>",
            progress_percentage,
            color,
            obj.progress * 100,
        )

    progress_bar.short_description = "Progress Bar"

    def property_link(self, obj):
        url = reverse(
            "admin:backup_backupproperty_change", args=[obj.property_primary_key]
        )
        return format_html('<a href="{}">{}</a>', url, obj.property_primary_key)

    property_link.short_description = "Property"


class JobStatusFilter(SimpleListFilter):
    title = "Job Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [
            ("PENDING", "Pending"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(BackupScrapingJob)
class BackupScrapingJobAdmin(admin.ModelAdmin):
    list_display = (
        "primary_key",
        "source",
        "status",
        "property_link",
        "task_link",
        "updated_at",
    )
    list_filter = ("source", JobStatusFilter, "updated_at")
    search_fields = (
        "primary_key",
        "url",
        "phone_number",
        "property_id",
        "scraped_property_id",
        "task_id",
    )
    readonly_fields = ("updated_at", "property_link", "task_link", "job_url")
    fieldsets = (
        (
            "Job Information",
            {"fields": ("primary_key", "url", "job_url", "source", "status")},
        ),
        ("Callback", {"fields": ("callback_url", "phone_number")}),
        (
            "Related Records",
            {
                "fields": (
                    "property_id",
                    "scraped_property_id",
                    "property_link",
                    "task_id",
                    "task_link",
                )
            },
        ),
        ("Metadata", {"fields": ("updated_at",)}),
    )

    def job_url(self, obj):
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank">View Source URL</a>', obj.url
            )
        return "-"

    job_url.short_description = "Source URL"

    def property_link(self, obj):
        if obj.property_id:
            url = reverse("admin:backup_backupproperty_change", args=[obj.property_id])
            return format_html('<a href="{}">{}</a>', url, obj.property_id)
        return "-"

    property_link.short_description = "Property"

    def task_link(self, obj):
        if obj.task_id:
            url = reverse("admin:backup_backupanalysistask_change", args=[obj.task_id])
            return format_html('<a href="{}">{}</a>', url, obj.task_id)
        return "-"

    task_link.short_description = "Analysis Task"
