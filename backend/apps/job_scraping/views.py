from django.shortcuts import render
from rest_framework import viewsets
from .models import Job
from .serializers import JobSerializer

# ReadOnlyModelViewSet is a view that provides default 'list' and 'detail' actions.
# ModelViewSet is a view that provides default 'list', 'create', 'retrieve', 'update', and 'destroy' actions.

class JobViewSet(viewsets.ReadOnlyModelViewSet): # A ViewSet lets you define a set of views (list, detail, etc.) in one class.
    """
    API endpoint that allows job data to be viewed.
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer



