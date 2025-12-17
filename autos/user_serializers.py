from rest_framework import serializers

from autos.models import AthleteInfo


class AthleteInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteInfo
        fields = ['user_id', 'weight']
