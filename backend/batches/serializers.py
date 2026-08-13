from rest_framework import serializers
from .models import Batch

class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['id', 'sample_id', 'batch_type', 'submitted_by', 
                 'status', 'result', 'partner_webhook', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class BatchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['sample_id', 'batch_type', 'submitted_by', 'partner_webhook']
    
    def validate_sample_id(self, value):
        if Batch.objects.filter(sample_id=value).exists():
            raise serializers.ValidationError("Batch with this sample_id already exists")
        return value

class BatchStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Batch.STATUS_CHOICES)