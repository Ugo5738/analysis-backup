from django.urls import path

from sdb import views

urlpatterns = [
    path("property/", views.SDBPropertyView.as_view(), name="property"),
    path("analysis-task/", views.SDBAnalysisTaskView.as_view(), name="analysis-task"),
    path("scraping-job/", views.SDBScrapingJobView.as_view(), name="scraping-job"),
    path("floorplan/", views.CompleteSDBFloorPlanView.as_view(), name="floorplan"),
    # New Endpoints for Consistency Check Listing
    path(
        "check/properties/",
        views.SDBPropertyListCheckView.as_view(),
        name="sdb-check-properties",
    ),
    path(
        "check/scraping-jobs/",
        views.SDBScrapingJobListCheckView.as_view(),
        name="sdb-check-scraping-jobs",
    ),
    path(
        "check/analysis-tasks/",
        views.SDBAnalysisTaskListCheckView.as_view(),
        name="sdb-check-analysis-tasks",
    ),
    path(
        "check/fp-analysis-results/",
        views.SDBFPAResultListCheckView.as_view(),
        name="sdb-check-fpa-results",
    ),
    path(
        "check/floorplans/",
        views.SDBFloorPlanListCheckView.as_view(),
        name="sdb-check-floorplans",
    ),
]
