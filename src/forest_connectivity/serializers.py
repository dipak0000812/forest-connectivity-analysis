from rest_framework import serializers
from .models import PipelineRun
from .validators import validate_location

class ForestConnectivityRequestSerializer(serializers.Serializer):
    state = serializers.CharField(required=True)
    district = serializers.CharField(required=True)
    block = serializers.CharField(required=True)
    lulc_year = serializers.CharField(default="2023_2024")
    edge_width_m = serializers.IntegerField(default=100, min_value=10, max_value=500)
    islet_area_ha = serializers.FloatField(default=1.0, min_value=0.1, max_value=10.0)
    notify_email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, data):
        # Validate spatial entity hierarchy
        validate_location(data.get('state'), data.get('district'), data.get('block'))
        return data

class PipelineRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineRun
        fields = '__all__'
