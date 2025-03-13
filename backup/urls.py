from django.urls import path

from backup import views

urlpatterns = [
    path("property/", views.BackupPropertyView.as_view(), name="property"),
    path(
        "analysis-task/", views.BackupAnalysisTaskView.as_view(), name="analysis-task"
    ),
    path("scraping-job/", views.BackupScrapingJobView.as_view(), name="scraping-job"),
    path("floorplan/", views.CompleteBackupFloorPlanView.as_view(), name="floorplan"),
]
