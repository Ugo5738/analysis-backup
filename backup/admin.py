from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html

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

# --- Filters (No changes needed here) ---


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


# --- ModelAdmins (Corrections applied below) ---


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
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
        image_count = len(obj.image_urls)
        display_limit = 5
        for i, url in enumerate(obj.image_urls):
            if i < display_limit:
                html += f'<img src="{url}" style="width: 150px; height: auto; object-fit: cover; border: 1px solid #ccc;" alt="Property Image {i+1}" />'

        if image_count > display_limit:
            html += f'<div style="width: 150px; height: 150px; display: flex; align-items: center; justify-content: center; background-color: #f0f0f0; border: 1px solid #ccc; font-size: 1.2em; color: #555;">+{image_count - display_limit} more</div>'

        html += "</div>"
        return format_html(html)

    image_preview.short_description = "Image Preview"


@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
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
        if obj.status == "FAILED":
            color = "#f44336"  # Red for failed
        elif obj.status == "PENDING":
            color = "#ff9800"  # Orange for pending
        return format_html(
            '<div style="width: 100%; background-color: #e0e0e0; border-radius: 5px; overflow: hidden;">'
            '<div style="height: 20px; width: {}%; background-color: {}; border-radius: 5px; text-align: center; color: white; line-height: 20px; font-size: 12px; font-weight: bold;">'
            "{:.1f}%</div></div>",
            progress_percentage,
            color,
            obj.progress * 100,
        )

    progress_bar.short_description = "Progress Bar"

    def property_link(self, obj):
        if obj.property_primary_key:
            try:
                url = reverse(
                    "admin:backup_property_change", args=[obj.property_primary_key]
                )
                return format_html('<a href="{}">{}</a>', url, obj.property_primary_key)
            except NoReverseMatch:
                # Handle cases where the property might not exist or the key is invalid
                return f"{obj.property_primary_key} (Link Error)"
        return "-"

    property_link.short_description = "Property"
    property_link.admin_order_field = "property_primary_key"


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
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
            try:
                url = reverse("admin:backup_property_change", args=[obj.property_id])
                return format_html('<a href="{}">{}</a>', url, obj.property_id)
            except NoReverseMatch:
                return f"{obj.property_id} (Link Error)"
        return "-"

    property_link.short_description = "Property"
    property_link.admin_order_field = "property_id"

    def task_link(self, obj):
        if obj.task_id:
            try:
                url = reverse("admin:backup_analysistask_change", args=[obj.task_id])
                return format_html('<a href="{}">{}</a>', url, obj.task_id)
            except NoReverseMatch:
                return f"{obj.task_id} (Link Error)"
        return "-"

    task_link.short_description = "Analysis Task"
    task_link.admin_order_field = "task_id"


@admin.register(FloorPlanAnalysisResult)
class FloorPlanAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "user_id", "property_id", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user_id", "property_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FloorPlan)
class FloorPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "floorplan_id", "original_url_link", "analysis_result")
    list_filter = ("analysis_result",)
    search_fields = ("floorplan_id",)
    readonly_fields = ("created_at", "updated_at", "original_url_link")
    list_select_related = ("analysis_result",)

    def original_url_link(self, obj):
        if obj.original_url:
            return format_html(
                '<a href="{0}" target="_blank">{0}</a>', obj.original_url
            )
        return "-"

    original_url_link.short_description = "Original URL"


@admin.register(AllFloorsData)
class AllFloorsDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "floor_plan_link",  # Changed for clarity
        "json_file_url_link",
        "csv_url_link",
        "total_area_csv_url_link",
        "image_labelme_side_by_side_url_link",
    )
    search_fields = ("floor_plan__floorplan_id",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "floor_plan_link",
        "json_file_url_link",
        "csv_url_link",
        "total_area_csv_url_link",
        "image_labelme_side_by_side_url_link",
    )
    list_select_related = ("floor_plan",)

    def floor_plan_link(self, obj):
        if obj.floor_plan:
            url = reverse("admin:backup_floorplan_change", args=[obj.floor_plan.id])
            return format_html(
                '<a href="{}">{} (ID: {})</a>',
                url,
                obj.floor_plan.floorplan_id,
                obj.floor_plan.id,
            )
        return "-"

    floor_plan_link.short_description = "Floor Plan"

    # Helper for creating links for URL fields
    def _make_link(self, url, text="View"):
        if url:
            return format_html(
                '<a href="{0}" target="_blank">{1}</a>',
                url,
                text if text != "View" else url,
            )
        return "-"

    def json_file_url_link(self, obj):
        return self._make_link(obj.json_file_url)

    json_file_url_link.short_description = "JSON URL"

    def csv_url_link(self, obj):
        return self._make_link(obj.csv_url)

    csv_url_link.short_description = "CSV URL"

    def total_area_csv_url_link(self, obj):
        return self._make_link(obj.total_area_csv_url)

    total_area_csv_url_link.short_description = "Total Area CSV URL"

    def image_labelme_side_by_side_url_link(self, obj):
        return self._make_link(obj.image_labelme_side_by_side_url)

    image_labelme_side_by_side_url_link.short_description = "Side-by-Side Image URL"


@admin.register(PlanFloor)
class PlanFloorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "floor",
        "floor_plan_link",
        "label_me_url_link",
    )  # Adjusted field names
    search_fields = ("floor_plan__floorplan_id", "floor")
    readonly_fields = (
        "created_at",
        "updated_at",
        "floor_plan_link",
        "label_me_url_link",
    )
    list_select_related = ("floor_plan",)

    def floor_plan_link(self, obj):
        if obj.floor_plan:
            url = reverse("admin:backup_floorplan_change", args=[obj.floor_plan.id])
            return format_html(
                '<a href="{}">{} (ID: {})</a>',
                url,
                obj.floor_plan.floorplan_id,
                obj.floor_plan.id,
            )
        return "-"

    floor_plan_link.short_description = "Floor Plan"

    def label_me_url_link(self, obj):
        if obj.label_me_url:
            return format_html(
                '<a href="{0}" target="_blank">{0}</a>', obj.label_me_url
            )
        return "-"

    label_me_url_link.short_description = "LabelMe URL"


@admin.register(CsvFloor)
class CsvFloorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "floor_name",
        "calculated_total_area_metric",
        "calculated_total_area_imperial",
        "all_floors_data_link",  # Renamed for consistency
    )
    list_filter = ("floor_name",)
    search_fields = (
        "floor_name",
        "all_floors_data__floor_plan__floorplan_id",
    )  # Added related search
    readonly_fields = ("created_at", "updated_at", "all_floors_data_link")
    list_select_related = ("all_floors_data__floor_plan",)  # Optimize query

    def all_floors_data_link(self, obj):
        if obj.all_floors_data:
            url = reverse(
                "admin:backup_allfloorsdata_change", args=[obj.all_floors_data.id]
            )
            fp_id = (
                obj.all_floors_data.floor_plan.floorplan_id
                if obj.all_floors_data.floor_plan
                else "N/A"
            )
            return format_html(
                '<a href="{}">AFD ID: {} (FP: {})</a>',
                url,
                obj.all_floors_data.id,
                fp_id,
            )
        return "-"

    all_floors_data_link.short_description = "All Floors Data"


@admin.register(CsvRoom)
class CsvRoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room_name",
        "csv_floor_link",
        "room_id",
    )  # Renamed for consistency
    search_fields = (
        "room_name",
        "csv_floor__floor_name",
        "room_id",
    )  # Added related search
    readonly_fields = ("created_at", "updated_at", "csv_floor_link")
    list_select_related = ("csv_floor__all_floors_data__floor_plan",)  # Optimize query

    def csv_floor_link(self, obj):
        if obj.csv_floor:
            url = reverse("admin:backup_csvfloor_change", args=[obj.csv_floor.id])
            return format_html(
                '<a href="{}">{} (ID: {})</a>',
                url,
                obj.csv_floor.floor_name,
                obj.csv_floor.id,
            )
        return "-"

    csv_floor_link.short_description = "CSV Floor"


@admin.register(CsvRoomPixelData)
class CsvRoomPixelDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "csv_room_link",  # Renamed for consistency
        "min_x_pixels",
        "min_y_pixels",
        "max_x_pixels",
        "max_y_pixels",
        "max_area_pixels",
        "actual_area_pixels",
        "pixel_ratio",
    )
    search_fields = ("csv_room__room_name",)  # Corrected field lookup
    readonly_fields = ("created_at", "updated_at", "csv_room_link")
    list_select_related = ("csv_room__csv_floor",)  # Optimize query

    def csv_room_link(self, obj):
        if obj.csv_room:
            url = reverse("admin:backup_csvroom_change", args=[obj.csv_room.id])
            return format_html(
                '<a href="{}">{} (ID: {})</a>',
                url,
                obj.csv_room.room_name,
                obj.csv_room.id,
            )
        return "-"

    csv_room_link.short_description = "CSV Room"


@admin.register(CsvRoomDimensions)
class CsvRoomDimensionsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "csv_room_link",  # Renamed for consistency
        "dimensions_imperial",
        "dimensions_metric",
        "max_area_metric",
        "max_area_imperial",
    )
    search_fields = ("csv_room__room_name",)  # Corrected field lookup
    readonly_fields = ("created_at", "updated_at", "csv_room_link")
    list_select_related = ("csv_room__csv_floor",)  # Optimize query

    # Reusing the link method from CsvRoomPixelDataAdmin
    csv_room_link = CsvRoomPixelDataAdmin.csv_room_link
    csv_room_link.short_description = "CSV Room"


@admin.register(CsvRoomScalingFactors)
class CsvRoomScalingFactorsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "csv_room_link",
        "scale_metric",
        "scale_imperial",
    )  # Renamed for consistency
    search_fields = ("csv_room__room_name",)  # Corrected field lookup
    readonly_fields = ("created_at", "updated_at", "csv_room_link")
    list_select_related = ("csv_room__csv_floor",)  # Optimize query

    # Reusing the link method from CsvRoomPixelDataAdmin
    csv_room_link = CsvRoomPixelDataAdmin.csv_room_link
    csv_room_link.short_description = "CSV Room"


@admin.register(AllFloorsCsvRawRow)
class AllFloorsCsvRawRowAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "all_floors_data_link",
        "floor_name",
        "room_name",
        "room_id",
        "is_segment",
        "created_at",
    )
    list_filter = ("floor_name", "is_segment", "created_at", "updated_at")
    search_fields = (
        "floor_name",
        "room_name",
        "room_id",
        "all_floors_data__floor_plan__floorplan_id",
    )
    # Make fields read-only as it's backup data
    readonly_fields = [f.name for f in AllFloorsCsvRawRow._meta.get_fields()]
    list_select_related = ("all_floors_data__floor_plan",)
    list_per_page = 100

    def all_floors_data_link(self, obj):
        if obj.all_floors_data:
            try:
                url = reverse(
                    "admin:backup_allfloorsdata_change", args=[obj.all_floors_data.id]
                )
                fp_id = (
                    obj.all_floors_data.floor_plan.floorplan_id
                    if obj.all_floors_data.floor_plan
                    else "N/A"
                )
                return format_html(
                    '<a href="{}">AFD ID: {} (FP: {})</a>',
                    url,
                    obj.all_floors_data.id,
                    fp_id,
                )
            except NoReverseMatch:
                return f"AFD ID: {obj.all_floors_data.id} (Link Error)"
        return "-"

    all_floors_data_link.short_description = "All Floors Data"
    all_floors_data_link.admin_order_field = "all_floors_data"


@admin.register(TotalAreaData)
class TotalAreaDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "all_floors_data_link",
        "area_name",
        "square_meters",
        "square_feet",
        "total_floors",
        "created_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("area_name", "all_floors_data__floor_plan__floorplan_id")
    readonly_fields = ("created_at", "updated_at", "all_floors_data_link")
    list_select_related = ("all_floors_data__floor_plan",)

    def all_floors_data_link(self, obj):  # DRY violation
        if obj.all_floors_data:
            try:
                url = reverse(
                    "admin:backup_allfloorsdata_change", args=[obj.all_floors_data.id]
                )
                fp_id = (
                    obj.all_floors_data.floor_plan.floorplan_id
                    if obj.all_floors_data.floor_plan
                    else "N/A"
                )
                return format_html(
                    '<a href="{}">AFD ID: {} (FP: {})</a>',
                    url,
                    obj.all_floors_data.id,
                    fp_id,
                )
            except NoReverseMatch:
                return f"AFD ID: {obj.all_floors_data.id} (Link Error)"
        return "-"

    all_floors_data_link.short_description = "All Floors Data"
    all_floors_data_link.admin_order_field = "all_floors_data"
