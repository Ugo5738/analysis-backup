# backup_service/backup/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backup.models import BackupAnalysisTask, BackupProperty, BackupScrapingJob
from backup.serializers import (
    BackupAnalysisTaskSerializer,
    BackupPropertySerializer,
    BackupScrapingJobSerializer,
)


class BackupPropertyView(APIView):
    """
    API endpoint to create, update, and list backup properties.
    """

    def post(self, request, *args, **kwargs):
        primary_key = request.data.get("primary_key")

        try:
            # If it already exists, we do an update
            backup_property = BackupProperty.objects.get(primary_key=primary_key)
            serializer = BackupPropertySerializer(
                backup_property, data=request.data, partial=True
            )
        except BackupProperty.DoesNotExist:
            # Otherwise create a new one
            serializer = BackupPropertySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # Return all backup properties (or filter as needed)
        properties = BackupProperty.objects.all()
        serializer = BackupPropertySerializer(properties, many=True)
        return Response(serializer.data)


class BackupAnalysisTaskView(APIView):
    """
    API endpoint to create and list backup analysis tasks.
    """

    def post(self, request, *args, **kwargs):
        serializer = BackupAnalysisTaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        tasks = BackupAnalysisTask.objects.all()
        serializer = BackupAnalysisTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class BackupScrapingJobView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BackupScrapingJobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        jobs = BackupScrapingJob.objects.all()
        serializer = BackupScrapingJobSerializer(jobs, many=True)
        return Response(serializer.data)
