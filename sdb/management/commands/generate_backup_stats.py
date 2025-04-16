import datetime

from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, F, Max, Min, Q, Sum  # Ensure Min, Max are imported
from django.db.models.functions import Length

# Import necessary models
from sdb.models import (  # Import others ONLY if directly queried for dates below
    AllFloorsCsvData,
    AllFloorsData,
    FloorPlan,
    FloorPlanAnalysisResult,
    Property,
    TotalAreasCsvData,
)


def get_date_range_for_queryset(queryset, model_class):
    """
    Safely calculates Min(created_at) and Max(updated_at) for a queryset.
    Handles potential missing fields and empty querysets.

    Args:
        queryset: The Django QuerySet to aggregate on.
        model_class: The Django Model class corresponding to the queryset.

    Returns:
        tuple: (min_created_date, max_updated_date), both can be None.
    """
    min_created_date = None
    max_updated_date = None

    if not queryset.exists():
        return None, None  # No records, no dates

    # Get Min Created At
    try:
        model_class._meta.get_field("created_at")  # Check if field exists
        aggregation = queryset.aggregate(min_date=Min("created_at"))
        min_created_date = aggregation.get("min_date")
    except FieldDoesNotExist:
        pass  # Model doesn't have created_at
    except Exception as e:
        # Catch potential errors during aggregation (though less likely without distinct)
        print(
            f"Warning: Error aggregating min created_at for {model_class.__name__}: {e}"
        )

    # Get Max Updated At
    try:
        model_class._meta.get_field("updated_at")  # Check if field exists
        aggregation = queryset.aggregate(max_date=Max("updated_at"))
        max_updated_date = aggregation.get("max_date")
    except FieldDoesNotExist:
        pass  # Model doesn't have updated_at
    except Exception as e:
        print(
            f"Warning: Error aggregating max updated_at for {model_class.__name__}: {e}"
        )

    return min_created_date, max_updated_date


# Helper to format output string
def format_output(label, count, min_created, max_updated):
    min_str = min_created.strftime("%Y-%m-%d %H:%M:%S") if min_created else "N/A"
    max_str = max_updated.strftime("%Y-%m-%d %H:%M:%S") if max_updated else "N/A"
    return f"{label}: {count} (Earliest Created: {min_str}, Latest Updated: {max_str})"


class Command(BaseCommand):
    help = "Generates statistics report for the application data, including date ranges per statistic."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "--- Generating Application Statistics (with Date Ranges per Stat) ---"
            )
        )

        try:
            # --- Property & Scraping Stats ---
            self.stdout.write(self.style.SUCCESS("\n--- Property & Scraping Stats ---"))

            # 1. Number of property URLs (Total Properties)
            all_properties_qs = Property.objects.all()
            total_properties_count = all_properties_qs.count()
            min_c, max_u = get_date_range_for_queryset(all_properties_qs, Property)
            self.stdout.write(
                format_output(
                    "Number of property URLs", total_properties_count, min_c, max_u
                )
            )

            # 2. Number of properties with a Gmail Source
            gmail_source_qs = Property.objects.filter(analysis_source="email")
            email_source_count = gmail_source_qs.count()
            min_c, max_u = get_date_range_for_queryset(gmail_source_qs, Property)
            self.stdout.write(
                format_output(
                    "Number of properties with a Gmail Source",
                    email_source_count,
                    min_c,
                    max_u,
                )
            )

            # 3. Number of properties scraped (Same as total properties in this context)
            # We already calculated this and its date range above
            self.stdout.write(
                format_output(
                    "Number of properties scraped (in sdb)",
                    total_properties_count,
                    *get_date_range_for_queryset(all_properties_qs, Property),
                )
            )

            # 4. Number of properties which are Sales
            sales_qs = Property.objects.filter(listing_type__icontains="sale")
            properties_sales_count = sales_qs.count()
            min_c, max_u = get_date_range_for_queryset(sales_qs, Property)
            self.stdout.write(
                format_output(
                    "Number of properties which are Sales",
                    properties_sales_count,
                    min_c,
                    max_u,
                )
            )

            # 5. Number of properties which are Lettings
            lettings_qs = Property.objects.filter(listing_type__icontains="letting")
            properties_lettings_count = lettings_qs.count()
            min_c, max_u = get_date_range_for_queryset(lettings_qs, Property)
            self.stdout.write(
                format_output(
                    "Number of properties which are Lettings",
                    properties_lettings_count,
                    min_c,
                    max_u,
                )
            )

            # --- Photo Stats ---
            self.stdout.write(self.style.SUCCESS("\n--- Photo Stats ---"))

            # 6. Number of properties with Photos
            photos_filter = (
                ~Q(image_urls__isnull=True) & ~Q(image_urls="[]") & ~Q(image_urls="{}")
            )
            properties_with_photos_qs = Property.objects.filter(photos_filter)
            properties_with_photos_count = properties_with_photos_qs.count()
            min_c, max_u = get_date_range_for_queryset(
                properties_with_photos_qs, Property
            )
            self.stdout.write(
                format_output(
                    "Number of properties with Photos",
                    properties_with_photos_count,
                    min_c,
                    max_u,
                )
            )

            # 7. Number of photos scraped
            # Date range is based on the *properties* having photos, not individual photo URLs
            total_photos_scraped = 0
            photo_props_values = properties_with_photos_qs.values_list(
                "image_urls", flat=True
            )  # Reuse the QS
            for url_list in photo_props_values.iterator():
                if isinstance(url_list, list):
                    total_photos_scraped += len(url_list)
            # Reuse the date range calculated for properties_with_photos
            min_c_photos, max_u_photos = get_date_range_for_queryset(
                properties_with_photos_qs, Property
            )
            self.stdout.write(
                format_output(
                    "Number of photos scraped",
                    total_photos_scraped,
                    min_c_photos,
                    max_u_photos,
                )
            )

            # 11. Number of Photos analysed (based on overall_analysis)
            photos_analysed_filter = ~Q(overall_analysis__isnull=True) & ~Q(
                overall_analysis={}
            )
            properties_photos_analysed_qs = Property.objects.filter(
                photos_analysed_filter
            )
            properties_photos_analysed_count = properties_photos_analysed_qs.count()
            min_c, max_u = get_date_range_for_queryset(
                properties_photos_analysed_qs, Property
            )
            self.stdout.write(
                format_output(
                    "Number of Properties with Photos analysed",
                    properties_photos_analysed_count,
                    min_c,
                    max_u,
                )
            )

            # --- Floorplan Stats ---
            self.stdout.write(self.style.SUCCESS("\n--- Floorplan Stats ---"))

            # 8. Number of properties with floorplans
            floorplans_filter = (
                ~Q(floorplan_urls__isnull=True)
                & ~Q(floorplan_urls="[]")
                & ~Q(floorplan_urls="{}")
            )
            properties_with_floorplans_qs = Property.objects.filter(floorplans_filter)
            properties_with_floorplans_count = properties_with_floorplans_qs.count()
            min_c, max_u = get_date_range_for_queryset(
                properties_with_floorplans_qs, Property
            )
            self.stdout.write(
                format_output(
                    "Number of properties with floorplans (based on URL list)",
                    properties_with_floorplans_count,
                    min_c,
                    max_u,
                )
            )

            # 9. Number of floorplans (distinct FloorPlan records)
            all_floorplan_records_qs = FloorPlan.objects.all()
            total_floorplans_count = all_floorplan_records_qs.count()
            # Use FloorPlan model for date range here
            min_c, max_u = get_date_range_for_queryset(
                all_floorplan_records_qs, FloorPlan
            )
            self.stdout.write(
                format_output(
                    "Number of Floorplan records", total_floorplans_count, min_c, max_u
                )
            )

            # 10. Number of properties with overall conditions
            overall_conditions_filter = ~Q(overall_condition__isnull=True) & ~Q(
                overall_condition={}
            )
            properties_with_overall_conditions_qs = Property.objects.filter(
                overall_conditions_filter
            )
            properties_with_overall_conditions_count = (
                properties_with_overall_conditions_qs.count()
            )
            min_c, max_u = get_date_range_for_queryset(
                properties_with_overall_conditions_qs, Property
            )
            self.stdout.write(
                format_output(
                    "Number of properties with overall conditions populated",
                    properties_with_overall_conditions_count,
                    min_c,
                    max_u,
                )
            )

            # --- Analysis Stages ---
            self.stdout.write(self.style.SUCCESS("\n--- Analysis Stages ---"))

            # 12. Number of properties with an Analysis Task initiated (using AnalysisTask)
            # Get distinct property keys from AnalysisTask, excluding tasks not linked to a property
            distinct_prop_keys_from_tasks = (
                AnalysisTask.objects.exclude(property_primary_key__isnull=True)
                .values_list("property_primary_key", flat=True)
                .distinct()
            )
            properties_basic_fp_analysis_count = (
                distinct_prop_keys_from_tasks.count()
            )  # Count distinct property keys

            # Get date range from *all* AnalysisTask records for these distinct properties
            # Note: AnalysisTask model only has updated_at defined in the snippet
            if (
                properties_basic_fp_analysis_count > 0
            ):  # Only query if we found properties
                analysis_tasks_for_properties_qs = AnalysisTask.objects.filter(
                    property_primary_key__in=list(distinct_prop_keys_from_tasks)
                )
                min_c, max_u = get_date_range_for_queryset(
                    analysis_tasks_for_properties_qs, AnalysisTask
                )
            else:
                min_c, max_u = None, None  # No properties found, so no date range

            # Update the label to reflect the source model
            self.stdout.write(
                format_output(
                    "Number of properties with an Analysis Task initiated",
                    properties_basic_fp_analysis_count,
                    min_c,
                    max_u,
                )
            )

            # 13. Number of properties with Text sentiment reviewed
            text_sentiment_filter = ~Q(sentiment_analysis__isnull=True) & ~Q(
                sentiment_analysis={}
            )
            properties_text_sentiment_qs = Property.objects.filter(
                text_sentiment_filter
            )
            properties_text_sentiment_count = properties_text_sentiment_qs.count()
            min_c, max_u = get_date_range_for_queryset(
                properties_text_sentiment_qs, Property
            )
            self.stdout.write(
                format_output(
                    "Number of properties with Text sentiment reviewed",
                    properties_text_sentiment_count,
                    min_c,
                    max_u,
                )
            )

            # 14. Number of properties with an AI Floorplan Analysis (has FloorPlan record)
            # FIX: Avoid distinct + aggregate. Get relevant FPAR IDs then filter.
            ai_fpar_ids = (
                FloorPlanAnalysisResult.objects.filter(sdb_floor_plans__isnull=False)
                .values_list("id", flat=True)
                .distinct()
            )  # Get IDs of FPARs linked to FloorPlans
            # Count distinct *properties* linked to these FPARs
            properties_ai_fp_analysis_count = (
                FloorPlanAnalysisResult.objects.filter(id__in=list(ai_fpar_ids))
                .values_list("property_id", flat=True)
                .distinct()
                .count()
            )
            # Get date range from the FPAR records themselves
            ai_fp_analysis_qs = FloorPlanAnalysisResult.objects.filter(
                id__in=list(ai_fpar_ids)
            )
            min_c, max_u = get_date_range_for_queryset(
                ai_fp_analysis_qs, FloorPlanAnalysisResult
            )
            self.stdout.write(
                format_output(
                    "Number of properties with an AI Floorplan Analysis (has FloorPlan record)",
                    properties_ai_fp_analysis_count,
                    min_c,
                    max_u,
                )
            )

            # 15. Number of properties with AI Floorplan Analysis - with allfloors CSV
            allfloors_csv_filter = ~Q(csv_url__isnull=True) & ~Q(csv_url="")
            allfloors_csv_qs = AllFloorsData.objects.filter(
                allfloors_csv_filter
            )  # Get relevant AllFloorsData
            # Count distinct properties linked
            prop_ids_allfloors_csv = allfloors_csv_qs.values_list(
                "floor_plan__analysis_result__property_id", flat=True
            ).distinct()
            properties_ai_fp_allfloors_csv_count = prop_ids_allfloors_csv.count()
            # Get date range from the AllFloorsData records meeting the criteria
            min_c, max_u = get_date_range_for_queryset(allfloors_csv_qs, AllFloorsData)
            self.stdout.write(
                format_output(
                    "Number of properties with AI Floorplan Analysis - with allfloors CSV",
                    properties_ai_fp_allfloors_csv_count,
                    min_c,
                    max_u,
                )
            )

            # 16. Number of properties with AI Floorplan Analysis - AllFloorsCsvData
            # Note: Renamed from "with allfloors CSV AllFloorsCsvData" for clarity
            allfloors_raw_rows_qs = AllFloorsData.objects.filter(
                all_floors_csv_data__isnull=False
            ).distinct()  # Distinct AllFloorsData linked to raw rows
            # Count distinct properties linked
            prop_ids_raw_rows = allfloors_raw_rows_qs.values_list(
                "floor_plan__analysis_result__property_id", flat=True
            ).distinct()
            properties_ai_fp_raw_rows_count = prop_ids_raw_rows.count()
            # Get date range from the AllFloorsData records linked to raw rows
            min_c, max_u = get_date_range_for_queryset(
                allfloors_raw_rows_qs, AllFloorsData
            )
            self.stdout.write(
                format_output(
                    "Number of properties with AI Floorplan Analysis - AllFloorsCsvData data present",
                    properties_ai_fp_raw_rows_count,
                    min_c,
                    max_u,
                )
            )

            # 17. Number of properties with AI Floorplan Analysis - total areas CSV
            totalarea_csv_filter = ~Q(total_area_csv_url__isnull=True) & ~Q(
                total_area_csv_url=""
            )
            totalarea_csv_qs = AllFloorsData.objects.filter(
                totalarea_csv_filter
            )  # Get relevant AllFloorsData
            # Count distinct properties linked
            prop_ids_total_area = totalarea_csv_qs.values_list(
                "floor_plan__analysis_result__property_id", flat=True
            ).distinct()
            properties_ai_fp_total_area_count = prop_ids_total_area.count()
            # Get date range from the AllFloorsData records meeting the criteria
            min_c, max_u = get_date_range_for_queryset(totalarea_csv_qs, AllFloorsData)
            self.stdout.write(
                format_output(
                    "Number of properties with AI Floorplan Analysis - total areas CSV present",
                    properties_ai_fp_total_area_count,
                    min_c,
                    max_u,
                )
            )

        except Exception as e:
            # Catch potential errors during querying or calculation
            raise CommandError(f"An error occurred while generating statistics: {e}")

        self.stdout.write(
            self.style.SUCCESS("\n--- Statistics Report Generation Complete ---")
        )
