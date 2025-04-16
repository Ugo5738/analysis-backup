from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from sdb.models import AnalysisTask, Property, ScrapingJob
from sdb.serializers import (
    AnalysisTaskSerializer,
    CompletesdbFloorPlanSerializer,
    PropertySerializer,
    ScrapingJobSerializer,
)


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
        serializer = ScrapingJobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
