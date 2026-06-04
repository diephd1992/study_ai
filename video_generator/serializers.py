from rest_framework import serializers
from .models import VideoRequest, ProcessingLog


class ProcessingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingLog
        fields = ['id', 'message', 'log_type', 'created_at']
        read_only_fields = ['created_at']


class VideoRequestSerializer(serializers.ModelSerializer):
    logs = ProcessingLogSerializer(many=True, read_only=True, source='logs')
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = VideoRequest
        fields = [
            'id',
            'user_username',
            'title',
            'description',
            'image',
            'text_prompt',
            'duration',
            'fps',
            'status',
            'video_file',
            'thumbnail',
            'error_message',
            'processing_time',
            'created_at',
            'updated_at',
            'started_at',
            'completed_at',
            'logs',
        ]
        read_only_fields = [
            'status',
            'video_file',
            'thumbnail',
            'error_message',
            'processing_time',
            'created_at',
            'updated_at',
            'started_at',
            'completed_at',
            'logs',
        ]


class VideoRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer để tạo video request"""

    class Meta:
        model = VideoRequest
        fields = [
            'title',
            'description',
            'image',
            'text_prompt',
            'duration',
            'fps',
        ]


class VideoRequestStatusSerializer(serializers.ModelSerializer):
    """Serializer để kiểm tra status"""

    class Meta:
        model = VideoRequest
        fields = [
            'id',
            'title',
            'status',
            'video_file',
            'thumbnail',
            'error_message',
            'processing_time',
            'created_at',
            'completed_at',
        ]
