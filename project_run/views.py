from django.http import JsonResponse

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