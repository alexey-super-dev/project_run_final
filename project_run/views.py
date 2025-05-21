from django.http import JsonResponse
from rest_framework import viewsets
from project_run.models import Run
from project_run.serializers import RunSerializer
from django.conf import settings

def company_details(request):
    """
    API endpoint that returns company details in JSON format.
    """
    data = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS
    }
    return JsonResponse(data)

class RunViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows runs to be viewed or edited.
    """
    queryset = Run.objects.all()
    serializer_class = RunSerializer
