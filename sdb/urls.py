from django.urls import path

from sdb import views

urlpatterns = [
    path("property/", views.SDBPropertyView.as_view(), name="property"),
    path("analysis-task/", views.SDBAnalysisTaskView.as_view(), name="analysis-task"),
    path("scraping-job/", views.SDBScrapingJobView.as_view(), name="scraping-job"),
    path("floorplan/", views.CompleteSDBFloorPlanView.as_view(), name="floorplan"),
]
