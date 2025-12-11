from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import viewsets

from autos.models import AthleteInfo
from autos.serializers import AthleteInfoSerializer


class AthleteInfoViewSet(viewsets.ModelViewSet):
    queryset = AthleteInfo.objects.all()
    serializer_class = AthleteInfoSerializer
    lookup_field = 'user_id'  # Use the native user ID for lookup

    def get_object(self):
        user_id = self.kwargs.get(self.lookup_field)
        user = get_object_or_404(User, id=user_id)
        user_info, _ = AthleteInfo.objects.get_or_create(user=user)
        return user_info
