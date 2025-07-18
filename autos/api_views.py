from rest_framework import viewsets

from autos.models import Run
from autos.serializers import RunSerializer
from decouple import config, Csv


class RunsAPIViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
