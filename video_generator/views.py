"""
API Views cho Video Generator
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import VideoRequest, ProcessingLog
from .serializers import (
    VideoRequestSerializer,
    VideoRequestCreateSerializer,
    VideoRequestStatusSerializer,
    ProcessingLogSerializer
)
from .services.replicate_service import (
    generate_video_with_replicate,
    get_video_status
)
from .services.image_processor import (
    create_thumbnail,
    validate_image
)
from .services.text_processor import (
    validate_prompt,
    optimize_prompt,
    get_prompt_suggestions,
)

logger = logging.getLogger(__name__)


class VideoRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet để quản lý Video Requests

    Endpoints:
    - POST /api/videos/ - Tạo video mới
    - GET /api/videos/ - Danh sách videos
    - GET /api/videos/{id}/ - Chi tiết video
    - GET /api/videos/{id}/status/ - Kiểm tra trạng thái
    - POST /api/videos/validate-prompt/ - Kiểm tra prompt
    - POST /api/videos/suggestions/ - Gợi ý cải thiện prompt
    """

    queryset = VideoRequest.objects.all()
    serializer_class = VideoRequestSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Chỉ trả về videos của user hiện tại"""
        return VideoRequest.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """Lưu user khi tạo video"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def create_video(self, request):
        """
        Tạo video mới

        POST /api/videos/create_video/
        {
            "title": "My Video",
            "description": "A test video",
            "image": <file>,
            "text_prompt": "A cat dancing",
            "duration": 5,
            "fps": 8
        }
        """
        serializer = VideoRequestCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate image
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Image file là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = request.FILES['image']
        image_path = image_file.temporary_file_path()

        is_valid, error_msg = validate_image(image_path)
        if not is_valid:
            return Response(
                {'error': f'Image không hợp lệ: {error_msg}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate prompt
        text_prompt = request.data.get('text_prompt', '')
        is_valid, error_msg, warning_msg = validate_prompt(text_prompt)

        if not is_valid:
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Tạo video request
        video_request = serializer.save(user=request.user)

        # Optimize prompt
        optimized_prompt = optimize_prompt(text_prompt)
        video_request.text_prompt = optimized_prompt
        video_request.save()

        # Tạo thumbnail (background task trong thực tế nên dùng Celery)
        create_thumbnail(video_request.id)

        # Bắt đầu xử lý video (nên dùng Celery/task queue)
        logger.info(f"🎬 Bắt đầu xử lý video {video_request.id}")
        success = generate_video_with_replicate(video_request.id)

        if not success:
            return Response(
                {
                    'id': video_request.id,
                    'warning': 'Video đã được tạo nhưng có lỗi trong xử lý'
                },
                status=status.HTTP_202_ACCEPTED
            )

        response_serializer = VideoRequestSerializer(video_request)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Kiểm tra trạng thái video

        GET /api/videos/{id}/status/
        """
        video_request = self.get_object()
        serializer = VideoRequestStatusSerializer(video_request)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Lấy processing logs

        GET /api/videos/{id}/logs/
        """
        video_request = self.get_object()
        logs = ProcessingLog.objects.filter(video_request=video_request).order_by('-created_at')
        serializer = ProcessingLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def validate_prompt(self, request):
        """
        Kiểm tra prompt

        POST /api/videos/validate_prompt/
        {
            "text_prompt": "A cat dancing"
        }
        """
        prompt = request.data.get('text_prompt', '')

        is_valid, error_msg, warning_msg = validate_prompt(prompt)

        if not is_valid:
            return Response(
                {
                    'valid': False,
                    'error': error_msg
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        optimized = optimize_prompt(prompt)
        suggestions = get_prompt_suggestions(prompt)

        return Response({
            'valid': True,
            'original': prompt,
            'optimized': optimized,
            'warning': warning_msg,
            'suggestions': suggestions
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def suggestions(self, request):
        """
        Nhận gợi ý cải thiện prompt

        POST /api/videos/suggestions/
        {
            "text_prompt": "A cat"
        }
        """
        prompt = request.data.get('text_prompt', '')

        if not prompt:
            return Response(
                {'error': 'Prompt không được trống'},
                status=status.HTTP_400_BAD_REQUEST
            )

        suggestions = get_prompt_suggestions(prompt)
        optimized = optimize_prompt(prompt)

        return Response({
            'original': prompt,
            'optimized': optimized,
            'suggestions': suggestions
        })

    @action(detail=False, methods=['get'])
    def my_videos(self, request):
        """
        Danh sách videos của user

        GET /api/videos/my_videos/
        """
        videos = self.get_queryset()

        # Filter by status nếu có
        status_filter = request.query_params.get('status')
        if status_filter:
            videos = videos.filter(status=status_filter)

        serializer = VideoRequestSerializer(videos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Thống kê videos của user

        GET /api/videos/stats/
        """
        videos = self.get_queryset()

        stats = {
            'total': videos.count(),
            'completed': videos.filter(status='completed').count(),
            'processing': videos.filter(status='processing').count(),
            'pending': videos.filter(status='pending').count(),
            'failed': videos.filter(status='failed').count(),
            'average_processing_time': 0,
        }

        completed = videos.filter(status='completed', processing_time__isnull=False)
        if completed.exists():
            total_time = sum(v.processing_time for v in completed)
            stats['average_processing_time'] = total_time / completed.count()

        return Response(stats)
