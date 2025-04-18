from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from pabackup_service.config.logging_config import configure_logger
from sdb.models import AnalysisTask, Property, ScrapingJob
from sdb.serializers import (
    AnalysisTaskSerializer,
    CompletesdbFloorPlanSerializer,
    PropertySerializer,
    ScrapingJobSerializer,
)

logger = configure_logger(__name__)


class SDBPropertyView(APIView):
    """
    API endpoint to create, update, and list sdb properties.
    """

    def post(self, request, *args, **kwargs):
        primary_key = request.data.get("primary_key")

        try:
            # If it already exists, we do an update
            sdb_property = Property.objects.get(primary_key=primary_key)
            serializer = PropertySerializer(
                sdb_property, data=request.data, partial=True
            )
        except Property.DoesNotExist:
            # Otherwise create a new one
            serializer = PropertySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # Return all sdb properties (or filter as needed)
        properties = Property.objects.all()
        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)


class SDBAnalysisTaskView(APIView):
    """
    API endpoint to create and list sdb analysis tasks.
    """

    def post(self, request, *args, **kwargs):
        serializer = AnalysisTaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        tasks = AnalysisTask.objects.all()
        serializer = AnalysisTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class SDBScrapingJobView(APIView):
    def post(self, request, *args, **kwargs):
        primary_key = request.data.get("primary_key")

        if primary_key is None:
            return Response(
                {"error": "Missing 'primary_key' in request data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Attempt to find an existing job in the SDB database
            sdb_job = ScrapingJob.objects.get(primary_key=primary_key)
            # If found, initialize serializer for an UPDATE operation
            # Use partial=True to allow updating only the fields provided,
            # though in a sync, you usually send all relevant fields.
            serializer = ScrapingJobSerializer(sdb_job, data=request.data, partial=True)
            operation = "update"
        except ScrapingJob.DoesNotExist:
            # If not found, initialize serializer for a CREATE operation
            serializer = ScrapingJobSerializer(data=request.data)
            operation = "create"
        except ValueError:
            # Handle cases where primary_key is not a valid integer/type
            return Response(
                {"error": f"Invalid 'primary_key' format: {primary_key}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            try:
                serializer.save()
                response_status = (
                    status.HTTP_200_OK
                    if operation == "update"
                    else status.HTTP_201_CREATED
                )
                return Response(serializer.data, status=response_status)
            except Exception as e:
                # Catch potential errors during save (less likely after is_valid)
                logger.error(
                    f"Error saving ScrapingJob PK={primary_key}: {e}", exc_info=True
                )
                return Response(
                    {"error": f"Failed to save scraping job: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # Log the validation errors for debugging
            logger.warning(
                f"Invalid data received for ScrapingJob PK={primary_key}: {serializer.errors}"
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        jobs = ScrapingJob.objects.all()
        serializer = ScrapingJobSerializer(jobs, many=True)
        return Response(serializer.data)


class CompleteSDBFloorPlanView(APIView):
    """
    API endpoint to receive and store the complete floorplan data.
    """

    def post(self, request, *args, **kwargs):
        serializer = CompletesdbFloorPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
