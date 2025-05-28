from django.http import JsonResponse
from rest_framework import viewsets
from project_run.models import Run
from project_run.serializers import RunSerializer

def company_details(request):
    """
    API endpoint that returns company details in JSON format.
    """
    data = {
        'company_name': 'Awesome Tech Solutions',
        'slogan': 'Innovating for a better tomorrow',
        'contacts': 'info@awesometech.com, +1-123-456-7890, 123 Tech Street, Silicon Valley'
    }
    return JsonResponse(data)

class RunViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows runs to be viewed or edited.
    """
    queryset = Run.objects.all()
    serializer_class = RunSerializer
